"""
HYPERREALM Google Calendar and Google Meet Integration Service.
Provides OAuth 2.0 authorization, token lifecycle management, free/busy querying,
and event creation with Google Meet conference generation.
"""
from __future__ import annotations

import logging
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from ..config import get_settings
from ..models import UserProfile, utcnow

logger = logging.getLogger("hyperrealm.calendar")

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"


class CalendarError(Exception):
    """Base exception for Google Calendar operations."""
    pass


class CalendarOAuthError(CalendarError):
    """Raised when OAuth flow or token refresh fails."""
    pass


class CalendarPermissionError(CalendarError):
    """Raised when calendar access is not permitted."""
    pass


class GoogleCalendarService:
    def __init__(self):
        self.settings = get_settings()

    @property
    def is_enabled(self) -> bool:
        return bool(
            self.settings.GOOGLE_CALENDAR_ENABLED
            and self.settings.GOOGLE_OAUTH_CLIENT_ID
            and self.settings.GOOGLE_OAUTH_CLIENT_SECRET
        )

    def get_authorization_url(self, user_id: str, state_extra: Optional[str] = None) -> str:
        """Generate Google OAuth 2.0 authorization URL for user consent."""
        if not self.is_enabled:
            raise CalendarError("Google Calendar integration is not enabled or OAuth credentials missing.")

        state = f"uid:{user_id}"
        if state_extra:
            state += f"|{state_extra}"

        params = {
            "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
            "redirect_uri": self.settings.GOOGLE_OAUTH_REDIRECT_URI,
            "response_type": "code",
            "scope": f"openid email {CALENDAR_SCOPE}",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        if not self.is_enabled:
            raise CalendarError("Google Calendar integration is disabled.")

        data = {
            "code": code,
            "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": self.settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uri": self.settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                logger.error("OAuth token exchange failed: %s %s", resp.status_code, resp.text)
                raise CalendarOAuthError(f"OAuth code exchange failed: {resp.text}")
            
            token_data = resp.json()
            now_ts = int(datetime.now(timezone.utc).timestamp())
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = now_ts + expires_in
            token_data["linked_at"] = utcnow().isoformat()
            return token_data

    async def get_valid_access_token(self, user: UserProfile) -> Optional[str]:
        """Retrieve valid access token for user, refreshing if expired."""
        tokens = user.oauth_tokens.get("google_calendar") if hasattr(user, "oauth_tokens") and user.oauth_tokens else None
        if not tokens:
            return None

        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        expires_at = tokens.get("expires_at", 0)
        now_ts = int(datetime.now(timezone.utc).timestamp())

        # If token still valid with at least 60s buffer, return it
        if access_token and (expires_at - now_ts) > 60:
            return access_token

        # Needs refresh
        if not refresh_token:
            logger.warning("User %s Google Calendar token expired and no refresh token available.", user.id)
            return None

        data = {
            "refresh_token": refresh_token,
            "client_id": self.settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": self.settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=data)
            if resp.status_code != 200:
                logger.error("Token refresh failed for user %s: %s", user.id, resp.text)
                return None

            new_tokens = resp.json()
            tokens["access_token"] = new_tokens.get("access_token")
            tokens["expires_at"] = now_ts + new_tokens.get("expires_in", 3600)
            if "refresh_token" in new_tokens:
                tokens["refresh_token"] = new_tokens["refresh_token"]
            return tokens["access_token"]

    async def check_user_calendar_availability(
        self,
        user: UserProfile,
        start_time: datetime,
        end_time: datetime,
        calendar_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Query Google Calendar freeBusy API for authenticated user."""
        token = await self.get_valid_access_token(user)
        if not token:
            return {
                "is_live": False,
                "available": True,
                "message": "Google Calendar not connected for user; availability checked against internal schedule.",
            }

        cal_id = calendar_id or self.settings.GOOGLE_CALENDAR_ID or "primary"
        time_min = start_time.astimezone(timezone.utc).isoformat() if start_time.tzinfo else f"{start_time.isoformat()}Z"
        time_max = end_time.astimezone(timezone.utc).isoformat() if end_time.tzinfo else f"{end_time.isoformat()}Z"

        payload = {
            "timeMin": time_min,
            "timeMax": time_max,
            "items": [{"id": cal_id}],
        }

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{GOOGLE_CALENDAR_API_BASE}/freeBusy", json=payload, headers=headers)
            if resp.status_code == 403:
                raise CalendarPermissionError("Calendar permission denied. Check access for this calendar ID.")
            if resp.status_code != 200:
                logger.warning("FreeBusy query failed: %s %s", resp.status_code, resp.text)
                return {"is_live": False, "available": True, "error": resp.text}

            data = resp.json()
            busy_slots = data.get("calendars", {}).get(cal_id, {}).get("busy", [])
            is_free = len(busy_slots) == 0
            return {
                "is_live": True,
                "available": is_free,
                "busy_slots": busy_slots,
                "calendar_id": cal_id,
            }

    async def create_event_with_meet(
        self,
        user: UserProfile,
        title: str,
        description: str,
        start_time: datetime,
        duration_minutes: int,
        attendee_emails: list[str],
        calendar_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a calendar event on Google Calendar and request a Google Meet link.
        Verifies conference creation before returning Meet link.
        """
        token = await self.get_valid_access_token(user)
        if not token:
            raise CalendarError("User has not authorized Google Calendar or token has expired.")

        cal_id = calendar_id or self.settings.GOOGLE_CALENDAR_ID or "primary"
        
        # Calculate naive/UTC times
        st = start_time.astimezone(timezone.utc) if start_time.tzinfo else start_time.replace(tzinfo=timezone.utc)
        from datetime import timedelta
        et = st + timedelta(minutes=duration_minutes)

        import uuid
        request_id = str(uuid.uuid4())

        event_payload = {
            "summary": title,
            "description": description,
            "start": {"dateTime": st.isoformat()},
            "end": {"dateTime": et.isoformat()},
            "attendees": [{"email": e} for e in attendee_emails if e],
            "conferenceData": {
                "createRequest": {
                    "requestId": request_id,
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        url = f"{GOOGLE_CALENDAR_API_BASE}/calendars/{cal_id}/events?conferenceDataVersion=1"
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(url, json=event_payload, headers=headers)
            if resp.status_code == 403:
                raise CalendarPermissionError(f"Permission denied creating event on calendar '{cal_id}': {resp.text}")
            if resp.status_code not in (200, 201):
                logger.error("Failed to create Google Calendar event: %s %s", resp.status_code, resp.text)
                raise CalendarError(f"Google Calendar event creation failed ({resp.status_code}): {resp.text}")

            event = resp.json()
            event_id = event.get("id")
            html_link = event.get("htmlLink")

            # Verify conference creation
            meet_link = None
            conf_data = event.get("conferenceData", {})
            entry_points = conf_data.get("entryPoints", [])
            for ep in entry_points:
                if ep.get("entryPointType") == "video":
                    meet_link = ep.get("uri")
                    break

            if not meet_link:
                # Fallback check on hangoutLink
                meet_link = event.get("hangoutLink")

            if not meet_link:
                conf_status = conf_data.get("createRequest", {}).get("status", {}).get("statusCode")
                logger.warning("Event created without confirmed Google Meet link. Status: %s", conf_status)
                # If conference creation failed, do not claim success for conference
                meet_link = None

            return {
                "is_live": True,
                "event_id": event_id,
                "calendar_id": cal_id,
                "html_link": html_link,
                "meet_link": meet_link,
                "conference_verified": bool(meet_link),
            }

    def check_status(self) -> dict[str, Any]:
        """Diagnostic check of Google Calendar and OAuth configuration."""
        configured = bool(
            self.settings.GOOGLE_CALENDAR_ENABLED
            and self.settings.GOOGLE_OAUTH_CLIENT_ID
            and self.settings.GOOGLE_OAUTH_CLIENT_SECRET
        )
        return {
            "enabled": self.settings.GOOGLE_CALENDAR_ENABLED,
            "configured": configured,
            "oauth_client_id_configured": bool(self.settings.GOOGLE_OAUTH_CLIENT_ID),
            "oauth_client_secret_configured": bool(self.settings.GOOGLE_OAUTH_CLIENT_SECRET),
            "redirect_uri": self.settings.GOOGLE_OAUTH_REDIRECT_URI,
            "calendar_id": self.settings.GOOGLE_CALENDAR_ID,
            "status": "ready" if configured else ("disabled" if not self.settings.GOOGLE_CALENDAR_ENABLED else "unconfigured"),
        }


_calendar_service: Optional[GoogleCalendarService] = None


def get_calendar_service() -> GoogleCalendarService:
    global _calendar_service
    if _calendar_service is None:
        _calendar_service = GoogleCalendarService()
    return _calendar_service
