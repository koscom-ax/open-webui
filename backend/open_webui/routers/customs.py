import uuid
import logging
from functools import wraps

from open_webui.models.auths import (
    Auths,
    UserModel,
)
from open_webui.models.config import Config
from open_webui.models.groups import GroupForm, GroupUpdateForm
from open_webui.models.users import Users
from open_webui.models.groups import Groups

from open_webui.constants import ERROR_MESSAGES
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from open_webui.utils.auth import create_session_response
from open_webui.utils.mfa import get_auth


log = logging.getLogger(__name__)

router = APIRouter()


def _exception_handler(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(str(e))
            raise HTTPException(status_code=500, detail=str(e))

    return wrapper


@router.get("/")
@_exception_handler
def custom_index():
    return {"message": "This is KOSCOM Custom API"}


@router.post("/auths/signin")
@_exception_handler
async def custom_signin(request: Request, response: Response):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    image = data.get("image")
    groups = data.get("groups")

    log.info(
        "[customs.signin] request received: email=%s name=%s groups=%s client=%s",
        email,
        name,
        groups,
        request.client.host if request.client else None,
    )

    user = await Users.get_user_by_email(email)
    log.info(
        "[customs.signin] user lookup by email=%s -> %s",
        email,
        f"id={user.id} role={user.role}" if isinstance(user, UserModel) else "NOT FOUND (will create)",
    )

    # Clear any existing cookie token
    response.delete_cookie("token")

    async def generate_and_set_cookie(user):
        # v0.12+: a token must carry the account's session_stamp or is_valid_token rejects it,
        # so issue it through upstream's session helper instead of create_token().
        # play_ax vouches for the identity server-to-server, which upstream models as 'trusted_header'.
        session = await create_session_response(
            request,
            user,
            response=response,
            set_cookie=True,
            source="trusted_header",
            auth=await get_auth(user.id),
        )
        token = session["token"]
        expires_at = session["expires_at"]
        log.info(
            "[customs.signin] issuing token: user_id=%s email=%s role=%s expires_at=%s token_prefix=%s",
            user.id,
            user.email,
            user.role,
            expires_at,
            (token[:16] + "...") if token else None,
        )
        return token, expires_at

    if not isinstance(user, UserModel):
        role = "admin" if (await Users.get_num_users()) == 0 else await Config.get("ui.default_user_role")
        user = await Auths.insert_new_auth(email.lower(), str(uuid.uuid4()), name, image, role)
        log.info(
            "[customs.signin] new user created: id=%s email=%s role=%s",
            getattr(user, "id", None),
            getattr(user, "email", None),
            getattr(user, "role", None),
        )

        try:
            if not user:
                raise HTTPException(500, detail=ERROR_MESSAGES.CREATE_USER_ERROR)

            if groups:
                # Process groups: ensure group exists and add user as a member.
                # NOTE: Group membership is stored in `GroupMember` table; group rows do not have `user_ids`.
                existing_groups = {grp.name: grp for grp in await Groups.get_all_groups()}
                for group_name in set(groups):
                    if group_name not in existing_groups:
                        group_form = GroupForm(
                            name=group_name,
                            description="",
                            permissions={},
                        )
                        new_group = await Groups.insert_new_group(user.id, group_form)
                        if new_group:
                            existing_groups[group_name] = new_group

                    group = existing_groups.get(group_name)
                    if group:
                        await Groups.add_users_to_group(id=group.id, user_ids=[user.id])

            token, expires_at = await generate_and_set_cookie(user)

        except Exception as e:
            log.exception("[customs.signin] failed during user/group setup, rolling back: %s", e)
            if isinstance(user, UserModel):
                await Auths.delete_auth_by_id(user.id)
            response.delete_cookie("token")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        token, expires_at = await generate_and_set_cookie(user)

    log.info(
        "[customs.signin] signin complete: user_id=%s email=%s role=%s expires_at=%s",
        user.id,
        user.email,
        user.role,
        expires_at,
    )

    return {
        "token": token,
        "token_type": "Bearer",
        "expires_at": expires_at,
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "profile_image_url": user.profile_image_url,
    }
