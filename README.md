# SQL_Visualiser

SQLVisualizer is a powerful and intuitive tool that transforms complex SQL queries into clear, graphical representations. By visualizing the structure and flow of your queries, it helps developers, database administrators, and data analysts better understand, optimize, and communicate their SQL logic.

## First-Time Setup

If you're using SQLVisualizer for the first time, follow these steps:

### 1. Install Python
Visit the official Python website: [Python Downloads](https://www.python.org/downloads/)  
version: - Python 3.12.4  

### 2. Install Graphviz
1. Download Graphviz from the [official Graphviz website](https://graphviz.org/download/)  
   version: - graphviz-11.0.0 (64-bit) ZIP archive [sha256] (contains all tools and libraries)   
3. Add the Graphviz bin folder path to your system:
   - Search for "edit the system environment variables" on your system
   - Include the bin folder path in both your system and user account variable paths

### 3. Install Required Libraries
Run the following commands in your terminal, VS Code, or preferred code editor:

```bash
pip install Flask
```
```bash
pip install graphviz
```
```bash
pip install Pillow
```
```bash
pip install sqlparse 
```

## How It Works

The process of SQL input to visualization follows these steps:

1. Getting input from `SQLViz.html` to `auth.py` file
2. Calling `SQL_parsing_module`, which returns a dictionary of lists
3. For each dictionary item, calling main functions in `structure_view.py` and `detail_view.py`
4. Returning an image and storing it in the dictionary of images
5. Sending the dictionary of images back to the HTML page
6. Creating dynamic tabs based on dictionary size and representing the output

## How to Run Application

After performing all the setup steps, you can run the application by following these instructions:

1. Open your terminal or command prompt
2. Navigate to the directory containing the application files
3. Run the following command:
```bash
Python main.py
```
4. After running the command, open the link to your local host in a web browser and add the following route:
```bash
/SQLViz
```
For example, if your local host is running on port 5000, the full URL would be:
```bash
http://localhost:5000/SQLViz
```
> Note: Ensure that you're in the correct directory and that all dependencies are properly installed before running the application.
