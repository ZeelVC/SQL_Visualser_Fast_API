import os
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

def enhance_image(image_path):
    img = Image.open(image_path)
    img = img.convert("RGBA")

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(0.5)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    modified_image_path = "modified_" + os.path.basename(image_path)
    img.save(modified_image_path, "PNG")

    return modified_image_path

def remove_background(image_path):
    img = Image.open(image_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    background_color = (255, 255, 255, 255)
    
    new_data = []
    for item in datas:
        if item[:3] == background_color[:3]:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    
    img.putdata(new_data)
    
    modified_image_path = "modified_" + os.path.basename(image_path)
    img.save(modified_image_path, "PNG")
    
    return modified_image_path

def change_image_color(image_path, target_color):
    img = Image.open(image_path)
    img = img.convert("RGBA")
    datas = img.getdata()
    target_color = Image.new("RGBA", (1, 1), target_color).getpixel((0, 0))
    new_data = [(target_color[0], target_color[1], target_color[2], item[3]) if item[3] != 0 else item for item in datas]
    img.putdata(new_data)
    modified_image_path = "colored_" + os.path.basename(image_path)
    img.save(modified_image_path, "PNG")
    return modified_image_path

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
    messages = []  # Initialize messages list

    Query = query
    query_dict = sql_to_dict(query)
    if query_dict:
        for query_num, query in query_dict.items():
            # Uncomment and adjust this block if you want to implement syntax checking
            # if check_syntax(query, 0):
            #     raise HTTPException(status_code=400, detail=f"SQL Syntax Error in Query {query_num}")

            dict_of_table_created = add_cte_table(dict_of_table_created, query, query_num)

            image_path1 = main1(query, dict_of_table_created)
            image_path2 = main2(query, dict_of_table_created)
            
            if image_path1 and os.path.exists(image_path1) and image_path2 and os.path.exists(image_path2):
                modified_image_path1 = remove_background(image_path1)
                modified_image_path2 = remove_background(image_path2)
                
                modified_image_path1 = enhance_image(modified_image_path1)
                modified_image_path2 = enhance_image(modified_image_path2)

                #modified_image_path1 = change_image_color(modified_image_path1, "#3266c0")
                #modified_image_path2 = change_image_color(modified_image_path2, "#3266c0")

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
                # Log the error or handle it as needed
                #print(f"Failed to generate visualization for Query {query_num}")
                messages.append(f"Failed to generate visualization for Query {query_num}")


    print(dict_of_table_created)

    return templates.TemplateResponse("SQLViz.html", {
        "request": request,
        "query": Query,
        "dict_of_images": dict_of_images
    })