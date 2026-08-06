"""RefreshToken entity (DATA_MODEL.md).

Encodes the one documented business rule: a token is active only while
unrevoked and unexpired, and revocation is a one-way, idempotent transition
(re-revoking an already-revoked token does not move its revoked_at).
"""

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class RefreshToken:
    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    user_agent: str | None
    ip_address: str | None

    def is_active(self, at: datetime) -> bool:
        return self.revoked_at is None and at < self.expires_at

    def revoke(self, at: datetime) -> None:
        if self.revoked_at is None:
            self.revoked_at = at
