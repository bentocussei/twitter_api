
import datetime
from typing import List
from urllib import response

from fastapi import APIRouter, Body, Path, Response
from fastapi import HTTPException
from fastapi import status

from sqlalchemy.exc import IntegrityError
from cryptography.fernet import Fernet

from core.models.user import users
from core.config.db import connection
from core.schemas.user import CreateUser, UserOut



user = APIRouter()

# Password encription configuration
key = Fernet.generate_key()
fernet = Fernet(key)

#Create a user
@user.post(
    path="/users",
    status_code=status.HTTP_201_CREATED,
    tags=["Users"],
    response_model=UserOut,
    summary="Sign Up a new user in the app"
)
def signup(user: CreateUser = Body(...)):
    """
    Sign Up
    
    This path operation registers a new user in the app.
    
    Parameters:
    - Request body parameters:
        - user: **UserRegister**
        
    Returns a json object with the information of the registered user and its credentials.
    - user: **UserOut**
    - access_token: **str**
    - access_token_expiration: **int**
    - refresh_token: **str**
    - refresh_token_expiration: **int**
    """
    
    new_user = user.dict()
    new_user["password"] = fernet.encrypt(user.password.encode("utf-8"))
    
    connection.execute(users.insert().values(new_user))
    
    res = connection.execute(users.select().where(users.columns.email == new_user["email"])).fetchone()
    
    return res


# Read All Users
@user.get(
    path="/users",
    tags=["Users"],
    summary="Get all Users from the app",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
    
)
def get_all_users():
    """
    Get All Users
    
    This path operation shows all users in the app.
    
    Parameters:
        - 
        
    Returns a list of json object with the information of all users.
    - id: **int**
    - first_name: **str**
    - last_name: **str**
    - email: **EmailStr**
    - created_at: **datetime**
    - updated_at: **datetime**
    """
    response = connection.execute(users.select()).fetchall()
   
    return response


# Read a user
@user.get(
    path="/users/{id}",
    tags=["Users"],
    status_code=status.HTTP_200_OK,
    response_model=UserOut,
    summary="Get a User from the app"
)
def get_user(
    id: int = Path(
        ...,
        gt=0,
        title="User ID",
        description="The user ID you want to get"
    )
):
    """
    Get user
        
    This path operation allows to get the information of a specific user.
    
    Parameters:
    - Path parameters:
        - id: **int**
        
    Returns a json object with the information of the user.
    - id: **int**
    - first_name: **str**
    - last_name: **str**
    - email: **EmailStr**
    - created_at: **datetime**
    - updated_at: **datetime**
    """
    
    res = connection.execute(users.select().where(users.columns.id == id)).fetchone()
    
    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return res


# Update a user
@user.put(
    path="/users/{id}",
    tags=["Users"],
    status_code=status.HTTP_200_OK,
    summary="Update a User in the app",
    response_model=UserOut
)
def update_user(
    id: int = Path(
        ...,
        gt=0,
        title="User ID",
        description="The user ID you want to update"
    ),
    user: CreateUser = Body(...)
):
    """
    Update user.
    
    This operation path operation updates the information of a specific user.
    Users can only update their own information.
    
    Parameters:
    - Path parameters:
        - id: **str**
    - Body parameters:
        - user: **CreateUser**
        
    Returns the information of the updated user.
    - id: **int**
    - first_name: **str**
    - last_name: **str**
    - email: **EmailStr**
    - created_at: **datetime**
    - updated_at: **datetime**
    """
    res = connection.execute(users.select().where(users.c.id == id)).fetchone()
    
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # if res.id != request_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="You are not allowed to perfom this action"
    #     )
    
    # Update user
    updated_user = {
        **res,
        **user.dict()
    }
    
    updated_user["password"] = fernet.encrypt(user.password.encode("utf-8"))
    
    # Save User
    try:
        connection.execute(users.update(users.c.id == id).values(**updated_user))
    except IntegrityError as e:
        
        if "Duplicate entry" in str(e) and "users.email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {user.email} already exist!"
            )
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Internal server error.') from e
        
    updated_user['updated_at'] = str(datetime.datetime.utcnow())
    
    return updated_user
    
    
# Delete a user
@user.delete(
    path="/users/{id}",
    tags=["Users"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a User from the app"
)
def delete_user(
    id: int = Path(
        ...,
        gt=0,
        title="User ID",
        description="The user ID you want to delete"
    )
):
    """
    Delete user
    
    This path operation deletes a specific user in the app.
    Users can only delete their own information.
    
    Parameters:
    - Path parameters:
        - id: **int**
        
    Returns:
        -
    """
    
    user_response = connection.execute(users.select().where(users.c.id == id)).fetchone()
    
    if user_response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
        
    # if user_response.id != request_user.id:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail='You are not allowed to perform this action'
    #     )
        
    # Delete user     
    connection.execute(users.delete().where(users.c.id == id))
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)