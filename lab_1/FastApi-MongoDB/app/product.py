import os
import re
import secrets
import uuid
from datetime import datetime
from typing import List

import aiofiles
from bson import ObjectId, errors
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse

from app.database import client
from app.schemas import CreateProduct, ReadProduct
from app.security import jwt_required
 
# create the product collection
Product = client.MarketPlace.products


# this is router for the products
product_router = APIRouter(prefix="/product", tags=["Products"])


def deserialize_product(product) -> dict:
    """
        Сonverts it to a dictionary

    Args:
        product: Product from the database

    Returns:
        dict: result dict
    """
    return {
        'id': str(product["_id"]),
        'name': product["name"],
        'description': product["description"],
        'price': product["price"],
        'is_available': product["is_available"],
        'images_url': product["images_url"],
        'create_at': product["created_at"],
        'category': product["category"],
        'location': product["location"],
        'condition': product["condition"],
        'currency': product["currency"],
        'views': product["views"]
        }


def remove_images(images_urls: List[str]):
    for image in images_urls:
        path = re.findall(r'static/.+', image.url)
        os.remove(str(path[0]))


def is_valid_objectid(object_id: str) -> bool:
    """
        Check if object_id can be converted to an ObjectId
    Args:
        object_id (str): The line to check

    Returns:
        bool: True or False
    """
    try:
        # Check if object_id can be converted to an ObjectId
        ObjectId(object_id)
        return True
    except errors.InvalidId:
        return False


@product_router.get("/",status_code=status.HTTP_200_OK, 
                    response_model=List[ReadProduct])
async def get_products():
    """ 
        list of all products

    Returns:
        List[ReadProduct]: List of all products
    """
    products = [deserialize_product(product) for product in Product.find()]   

    return products


@product_router.get("/{id}", status_code=status.HTTP_200_OK, 
                    response_model=ReadProduct)
async def get_product(id: str):
    """Get one product

    Args:
        id (str): id_product

    Returns:
        ReadProduct: The product corresponding to the ID.
    """
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    product = Product.find_one({"_id":ObjectId(id)})
    if product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    product["views"] = product["views"] + 1
    return deserialize_product(product)


@product_router.post("/", status_code=status.HTTP_201_CREATED, 
                     response_model=ReadProduct)
async def create_product(product: CreateProduct, 
                         Authorize: dict = Depends(jwt_required)):
    """
         Create a new product.

    Args:
        product (CreateProduct): Pydantic BaseModel
        Authorize (dict, optional): user data. Defaults to Depends(jwt_required).

    Returns:
        ReadProduct: created product
    """
    product=dict(product)
    product["created_at"] = datetime.today()
    product["is_available"] = True
    product["images_url"] = []
    product["user"] = Authorize["id"]
    product["views"] = 0
    new_product = Product.insert_one(product)
    new_product = Product.find_one({"_id": new_product.inserted_id})
    return deserialize_product(new_product)


@product_router.post("/upload/{id}", 
                     status_code=status.HTTP_201_CREATED)
async def upload_images(request: Request, id: str, 
                        images: List[UploadFile] = File(...),
                        Authorize: dict = Depends(jwt_required)):
    """
        Uploads images for the product

    Args:
        request (Request): HTTP
        id (str): Id product
        images (List[UploadFile], optional): list image. Defaults to File(...).
        Authorize (dict, optional): user data. Defaults to Depends(jwt_required).

    Returns:
        _type_: Confirmation of uploading images.
    """
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    product = Product.find_one({"_id": ObjectId(id)})
    if product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    if product["user"] != Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Unauthorized access")
    images_url = []
    for image in images:
        if image.content_type not in ['image/png','image/jpeg','image/jpg']:
            return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                 detail='the file must be image')
    for image in images:
            destination_file_path = "static/" + \
                secrets.token_hex(13) + image.filename 
            async with aiofiles.open(destination_file_path, 'wb') as out_file:
                 while content := await image.read(1024):  
                    await out_file.write(content) 
            images_url.append(request.base_url._url + destination_file_path)

    product.update_one({"$set": {"images_url": images_url}})
    return JSONResponse(content={"detail": "images uploaded"})


@product_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id: str, Authorize: dict = Depends(jwt_required)):
    """
        Deleting a product from the database

    Args:
        id (str): id product
        Authorize (dict, optional): user data. Defaults to Depends(jwt_required).

    Returns:
        _type_: message product deleted
    """
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    product = Product.find_one({"_id": ObjectId(id)})
    if product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Product not found")
    if product["user"] != Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Unauthorized access")
    # removing images from the server (static folder)
    image_urls = product["images_url"]
    await remove_images(image_urls)

    Product.delete_one({"_id": ObjectId(id)})
    return JSONResponse(content={"detail": "product deleted"})


@product_router.patch("/{id}", status_code=status.HTTP_202_ACCEPTED)
async def update_product(id: str, data: CreateProduct, 
                         Authorize: dict = Depends(jwt_required)):
    """
        updating a single product 

    Args:
        id (str): id product
        data (CreateProduct): information
        Authorize (dict, optional): user data. Defaults to Depends(jwt_required).

    Returns:
        _type_: New product
    """
    if not is_valid_objectid(id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    product=Product.find_one({"_id": ObjectId(id)})
    if product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="Product not found")
    if product["user"] != Authorize["id"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Unauthorized access")
    product.update_one({"$set": dict(data)})
    # product=Product.find_one_and_update({"_id":ObjectId(id)},{"$set":dict(data)})    
    
    # product_updated=Product.find_one({"_id":ObjectId(id)})
    return deserialize_product(product)
