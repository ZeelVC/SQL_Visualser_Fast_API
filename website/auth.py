import os
import re
import base64
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from PIL import Image, ImageEnhance
from .structure_view import main1, check_syntax
from .detail_view import main2
from .SQL_parsing_module import sql_to_dict

router = APIRouter()
templates = Jinja2Templates(directory="website/templates")

def add_cte_table(dict_of_cte_table, query, query_num):
    new_dict = dict_of_cte_table
    query = query.replace('\n', ' ').replace(', ', ',').replace(',', ', ')
    i = 0
    parsed = query.split()
    while i < len(parsed):
        if parsed[i].upper() == 'CREATE':
            create_table_str = ''
            while parsed[i].upper() != 'TABLE':
                i += 1
            i += 1
            while parsed[i].upper() != 'AS':
                if parsed[i][-1] == ',':
                    create_table_str += parsed[i] + '\n'
                else:
                    create_table_str += parsed[i]
                i += 1
            dict_of_cte_table[create_table_str] = query_num
        i += 1

    return new_dict

@router.get("/SQLViz", response_class=HTMLResponse)
async def sqlviz_get(request: Request):
    return templates.TemplateResponse("SQLViz.html", {"request": request, "query": "", "dict_of_images": {}})

@router.post("/SQLViz", response_class=HTMLResponse)
async def sqlviz_post(request: Request, query: str = Form(...)):
    dict_of_images = {}
    dict_of_table_created = {}
    messages = []

    Query = query

    # Trim whitespace from the query
    query = query.strip()
    
    # Define SQL clauses to look for
    clauses = [
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'JOIN', 
        'ON', 'ORDER', 'GROUP', 'HAVING', 'LIMIT', 'UNION', 'WITH'
    ]
    
    # Create regex pattern
    pattern = r'\b(' + '|'.join(clauses) + r')\b'
    
    # Function to replace matches with uppercase and newline
    def replace_func(match):
        return '\n' + match.group(0).upper()
    
    # Apply the regex replacement
    query = re.sub(pattern, replace_func, query, flags=re.IGNORECASE)
    
    # Ensure the query ends with a semicolon
    if not query.endswith(';'):
        query += ';'

    print("query after formatting it in auth.py file : ")
    print(query)
    query_dict = sql_to_dict(query)
    if query_dict:
        for query_num, query in query_dict.items():
            dict_of_table_created = add_cte_table(dict_of_table_created, query, query_num)

            image_path1 = main1(query, dict_of_table_created)
            image_path2 = main2(query, dict_of_table_created)
            
            if image_path1 and os.path.exists(image_path1) and image_path2 and os.path.exists(image_path2):
                # Process image 1
                img1 = Image.open(image_path1)
                img1 = img1.convert("RGBA")
                datas1 = img1.getdata()
                
                # Remove background for image 1
                new_data1 = []
                for item in datas1:
                    if item[:3] == (255, 255, 255):
                        new_data1.append((255, 255, 255, 0))
                    else:
                        new_data1.append(item)
                img1.putdata(new_data1)
                
                # Enhance image 1
                enhancer = ImageEnhance.Brightness(img1)
                img1 = enhancer.enhance(0.5)
                enhancer = ImageEnhance.Contrast(img1)
                img1 = enhancer.enhance(1.5)
                
                # Save modified image 1
                modified_image_path1 = "modified_" + os.path.basename(image_path1)
                img1.save(modified_image_path1, "PNG")

                # Process image 2
                img2 = Image.open(image_path2)
                img2 = img2.convert("RGBA")
                datas2 = img2.getdata()
                
                # Remove background for image 2
                new_data2 = []
                for item in datas2:
                    if item[:3] == (255, 255, 255):
                        new_data2.append((255, 255, 255, 0))
                    else:
                        new_data2.append(item)
                img2.putdata(new_data2)
                
                # Enhance image 2
                enhancer = ImageEnhance.Brightness(img2)
                img2 = enhancer.enhance(0.5)
                enhancer = ImageEnhance.Contrast(img2)
                img2 = enhancer.enhance(1.5)
                
                # Save modified image 2
                modified_image_path2 = "modified_" + os.path.basename(image_path2)
                img2.save(modified_image_path2, "PNG")

                # Read and encode images
                with open(modified_image_path1, 'rb') as image_file:
                    img_data1 = base64.b64encode(image_file.read()).decode('utf-8')
                with open(modified_image_path2, 'rb') as image_file:
                    img_data2 = base64.b64encode(image_file.read()).decode('utf-8')
                
                dict_of_images[query_num] = {
                    'tables_view': img_data1,
                    'query_view': img_data2
                }
                
                # Clean up temporary files
                os.remove(image_path1)
                os.remove(image_path2)
                os.remove(modified_image_path1)
                os.remove(modified_image_path2)
            else:
                messages.append(f"Failed to generate visualization for Query {query_num}")

    print(dict_of_table_created)

    return templates.TemplateResponse("SQLViz.html", {
        "request": request,
        "query": Query,
        "dict_of_images": dict_of_images
    })
