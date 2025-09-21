import yaml
import os
from typing import Dict, Any, Tuple
from urllib.parse import urlparse
from pathlib import Path

def get_button_variant_styles(variant: str, size: str, button_style: str) -> Dict[str, str]:
    base_styles = {
        "border": "none",
        "border-radius": "8px",
        "font-weight": "500",
        "cursor": "pointer",
        "transition": "all 0.2s ease",
        "text-decoration": "none",
        "display": "inline-block",
        "text-align": "center"
    }
    
    size_styles = {
        "small": {
            "padding": "6px 12px",
            "font-size": "0.875rem"
        },
        "medium": {
            "padding": "10px 20px",
            "font-size": "1rem"
        },
        "large": {
            "padding": "14px 28px",
            "font-size": "1.125rem"
        }
    }
    variant_colors = {
        "primary": {
            "solid": {
                "background-color": "#4dabf7 !important",
                "color": "#ffffff !important",
                "border": "2px solid #4dabf7 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#4dabf7 !important",
                "border": "2px solid #4dabf7 !important"
            },
            "ghost": {
                "background-color": "rgba(77, 171, 247, 0.1) !important",
                "color": "#4dabf7 !important",
                "border": "2px solid transparent !important"
            }
        },
        "secondary": {
            "solid": {
                "background-color": "#6c757d !important",
                "color": "#ffffff !important",
                "border": "2px solid #6c757d !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#6c757d !important",
                "border": "2px solid #6c757d !important"
            },
            "ghost": {
                "background-color": "rgba(108, 117, 125, 0.1) !important",
                "color": "#6c757d !important",
                "border": "2px solid transparent !important"
            }
        },
        "success": {
            "solid": {
                "background-color": "#28a745 !important",
                "color": "#ffffff !important",
                "border": "2px solid #28a745 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#28a745 !important",
                "border": "2px solid #28a745 !important"
            },
            "ghost": {
                "background-color": "rgba(40, 167, 69, 0.1) !important",
                "color": "#28a745 !important",
                "border": "2px solid transparent !important"
            }
        },
        "danger": {
            "solid": {
                "background-color": "#dc3545 !important",
                "color": "#ffffff !important",
                "border": "2px solid #dc3545 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#dc3545 !important",
                "border": "2px solid #dc3545 !important"
            },
            "ghost": {
                "background-color": "rgba(220, 53, 69, 0.1) !important",
                "color": "#dc3545 !important",
                "border": "2px solid transparent !important"
            }
        },
        "warning": {
            "solid": {
                "background-color": "#ffc107 !important",
                "color": "#212529 !important",
                "border": "2px solid #ffc107 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#ffc107 !important",
                "border": "2px solid #ffc107 !important"
            },
            "ghost": {
                "background-color": "rgba(255, 193, 7, 0.1) !important",
                "color": "#ffc107 !important",
                "border": "2px solid transparent !important"
            }
        },
        "info": {
            "solid": {
                "background-color": "#17a2b8 !important",
                "color": "#ffffff !important",
                "border": "2px solid #17a2b8 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#17a2b8 !important",
                "border": "2px solid #17a2b8 !important"
            },
            "ghost": {
                "background-color": "rgba(23, 162, 184, 0.1) !important",
                "color": "#17a2b8 !important",
                "border": "2px solid transparent !important"
            }
        },
        "light": {
            "solid": {
                "background-color": "#f8f9fa !important",
                "color": "#212529 !important",
                "border": "2px solid #f8f9fa !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#f8f9fa !important",
                "border": "2px solid #f8f9fa !important"
            },
            "ghost": {
                "background-color": "rgba(248, 249, 250, 0.1) !important",
                "color": "#f8f9fa !important",
                "border": "2px solid transparent !important"
            }
        },
        "dark": {
            "solid": {
                "background-color": "#343a40 !important",
                "color": "#ffffff !important",
                "border": "2px solid #343a40 !important"
            },
            "outline": {
                "background-color": "transparent !important",
                "color": "#343a40 !important",
                "border": "2px solid #343a40 !important"
            },
            "ghost": {
                "background-color": "rgba(52, 58, 64, 0.1) !important",
                "color": "#343a40 !important",
                "border": "2px solid transparent !important"
            }
        }
    }
    
    styles = base_styles.copy()
    styles.update(size_styles.get(size, size_styles["medium"]))
    styles.update(variant_colors.get(variant, variant_colors["primary"]).get(button_style, variant_colors["primary"]["solid"]))
    
    return styles

def is_local_path(path: str) -> bool:
    parsed = urlparse(path)
    return not parsed.scheme or parsed.scheme == 'file'

def path_to_file_url(path: str) -> str:
    try:
        print("\n=== Debug: Image Path Processing ===")
        print(f"Input path: {path}")
        
        path = path.strip().strip("'").strip('"')
        print(f"Cleaned path: {path}")
        
        if path.startswith('/'):
            path = path[1:]
            print(f"Removed leading slash: {path}")
        
        cwd = os.getcwd()
        print(f"Current working directory: {cwd}")
        
        abs_path = str(Path(cwd) / path)
        print(f"Absolute path: {abs_path}")
        
        if not os.path.exists(abs_path):
            print(f"❌ File not found at: {abs_path}")
            print(f"Directory contents of {os.path.dirname(abs_path)}:")
            try:
                print(os.listdir(os.path.dirname(abs_path)))
            except Exception as e:
                print(f"Could not list directory: {str(e)}")
            return path
            
        print(f"✅ File exists at: {abs_path}")
            
        path = abs_path.replace('\\', '/')
        print(f"Normalized slashes: {path}")
        
        if path[1] == ':':
            path = path[0] + ':' + path[2:]
            print(f"Fixed drive letter: {path}")
        
        if not path.startswith('file://'):
            path = 'file:///' + path
            print(f"Added file:// prefix: {path}")
            
        print(f"Final file URL: {path}")
        print("=== End Debug ===\n")
        return path
    except Exception as e:
        print(f"❌ Error converting path {path}: {str(e)}")
        return path

def style_dict_to_html(style_dict: Dict[str, str]) -> str:
    if not style_dict:
        return ""
    styles = [f"{k}: {v}" for k, v in style_dict.items()]
    return f' style="{"; ".join(styles)}"'

def render_component(component: Dict[str, Any]) -> str:
    if not isinstance(component, dict):
        return ""
        
    component_type = component.get("type", "").lower()
    style = style_dict_to_html(component.get("style", {}))
    text = component.get("text", "")
    if component_type == "header":
        return f"<h1{style}>{text}</h1>"
        
    elif component_type == "paragraph":
        return f"<p{style}>{text}</p>"
        
    elif component_type == "image":
        src = component.get("src", "")
        alt = component.get("alt", "")
        if is_local_path(src):
            src = path_to_file_url(src)
        return f'<img src="{src}" alt="{alt}"{style} onerror="this.onerror=null; this.src=\'data:image/svg+xml;charset=UTF-8,%3Csvg%20width%3D%22800%22%20height%3D%22600%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Crect%20width%3D%22800%22%20height%3D%22600%22%20fill%3D%22%23f0f0f0%22%2F%3E%3Ctext%20x%3D%2250%25%22%20y%3D%2250%25%22%20font-family%3D%22Arial%22%20font-size%3D%2230%22%20fill%3D%22%23999%22%20text-anchor%3D%22middle%22%20dominant-baseline%3D%22middle%22%3EImage%20not%20found%3C%2Ftext%3E%3C%2Fsvg%3E\';">'
        
    elif component_type == "list":
        items = component.get("items", [])
        if not items:
            return ""
            
        list_type = component.get("list-type", "none").lower()
        
        list_style = component.get("style", {}).copy()
        list_style["list-style-type"] = list_type
        
        list_style_str = style_dict_to_html(list_style)
        
        list_tag = "ol" if list_type in ["decimal", "decimal-leading-zero", "lower-roman", "upper-roman", "lower-alpha", "upper-alpha"] else "ul"
        
        list_html = [f'<{list_tag}{list_style_str}>']
        for item in items:
            if isinstance(item, dict):
                for key, value in item.items():
                    list_html.append(f"<li><strong>{key}:</strong> {value}</li>")
            else:
                list_html.append(f"<li>{item}</li>")
        list_html.append(f"</{list_tag}>")
        return f'<div{style}>{"".join(list_html)}</div>'
        
    elif component_type == "button":
        link = component.get("link", "#")
        variant = component.get("variant", "primary")
        size = component.get("size", "medium")
        button_style = component.get("button-style", "solid")
        custom_styles = component.get("style", {})
        
        variant_styles = get_button_variant_styles(variant, size, button_style)
        
        if custom_styles:
            variant_styles.update(custom_styles)
        
        variant_style_str = style_dict_to_html(variant_styles)
        
        return f'<div class="buttons"><a href="{link}"><button{variant_style_str}>{text}</button></a></div>'
        
    elif component_type == "section":
        children = component.get("children", [])
        section_html = [f'<section{style}>']
        
        if text:
            section_html.append(f'<div class="section-text">{text}</div>')
            
        if children:
            for child in children:
                section_html.append(render_component(child))
                
        section_html.append("</section>")
        return "".join(section_html)
        
    elif component_type == "div":
        children = component.get("children", [])
        div_html = [f'<div{style}>']
        
        if text:
            div_html.append(f'<div class="div-text">{text}</div>')
            
        if children:
            for child in children:
                div_html.append(render_component(child))
                
        div_html.append("</div>")
        return "".join(div_html)
        
    return ""

def yaml_to_html(yaml_text: str) -> Tuple[str, bool]:
    try:
        data = yaml.safe_load(yaml_text)
        if not data:
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebForge - Ready to Build</title>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .welcome-container {
            text-align: center;
            max-width: 600px;
            padding: 40px;
        }
        .welcome-title {
            color: #4dabf7;
            font-size: 3rem;
            font-weight: 600;
            margin-bottom: 20px;
        }
        .welcome-subtitle {
            color: #a0a0a0;
            font-size: 1.2rem;
            margin-bottom: 30px;
        }
        .welcome-description {
            color: #e0e0e0;
            font-size: 1rem;
            line-height: 1.8;
            margin-bottom: 40px;
        }
        .welcome-features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .feature-item {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #4dabf7;
        }
        .feature-title {
            color: #4dabf7;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .feature-desc {
            color: #a0a0a0;
            font-size: 0.9rem;
        }
        .load-example-container {
            margin-top: 40px;
            text-align: center;
        }
        .load-example-btn {
            background: linear-gradient(135deg, #4dabf7 0%, #339af0 100%);
            color: #ffffff;
            border: none;
            border-radius: 12px;
            padding: 18px 36px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            align-items: center;
            gap: 12px;
            box-shadow: 0 8px 25px rgba(77, 171, 247, 0.25);
            text-decoration: none;
            position: relative;
            overflow: hidden;
            min-width: 200px;
            justify-content: center;
        }
        .load-example-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }
        .load-example-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px rgba(77, 171, 247, 0.4);
            background: linear-gradient(135deg, #339af0 0%, #228be6 100%);
        }
        .load-example-btn:hover::before {
            left: 100%;
        }
        .load-example-btn:active {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(77, 171, 247, 0.3);
        }
        .btn-icon {
            font-size: 1.2rem;
        }
        .load-example-desc {
            color: #a0a0a0;
            font-size: 0.9rem;
            margin-top: 12px;
            margin-bottom: 0;
        }
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
        }
        .welcome-logo {
            max-width: 120px;
            max-height: 120px;
            width: auto;
            height: auto;
            border-radius: 12px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }
        .welcome-logo:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="welcome-container">
        <div class="logo-container">
            <img src="logo.png" alt="WebForge Logo" class="welcome-logo" onerror="this.style.display='none'">
        </div>
        <h1 class="welcome-title">Welcome to WebForge</h1>
        <p class="welcome-subtitle">Your YAML-powered webpage builder</p>
        <p class="welcome-description">
            Start building your webpage by writing YAML in the editor. 
            Use components like headers, paragraphs, images, buttons, and more to create beautiful pages.
        </p>
        <div class="welcome-features">
            <div class="feature-item">
                <div class="feature-title">Simple Syntax</div>
                <div class="feature-desc">Write clean YAML to define your page structure</div>
            </div>
            <div class="feature-item">
                <div class="feature-title">Live Preview</div>
                <div class="feature-desc">See your changes in real-time as you type</div>
            </div>
            <div class="feature-item">
                <div class="feature-title">Rich Components</div>
                <div class="feature-desc">Headers, images, buttons, lists, and more</div>
            </div>
            <div class="feature-item">
                <div class="feature-title">Custom Styling</div>
                <div class="feature-desc">Apply CSS styles to any component</div>
            </div>
        </div>
        <div class="load-example-container">
            <button class="load-example-btn" onclick="window.webforgeLoadExample()">
                <span class="btn-text">Load Example</span>
            </button>
            <p class="load-example-desc">Try our example to see what's possible</p>
        </div>
        <script>
            // Initialize WebChannel
            new QWebChannel(qt.webChannelTransport, function (channel) {
                window.webforge = channel.objects.webforge;
            });
            
            // Define the function that will be called by the button
            window.webforgeLoadExample = function() {
                if (window.webforge && window.webforge.loadExample) {
                    window.webforge.loadExample();
                } else {
                    console.log('WebForge bridge not available');
                }
            };
        </script>
    </div>
</body>
</html>""", True

        title = data.get("title", "Untitled Page")
        body_style = data.get("body", {}).get("style", {})
        body_text = data.get("body", {}).get("text", "")
        
        html_parts = [f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        h1 {{
            color: #4dabf7;
            font-size: 2.5em;
            font-weight: 600;
            margin: 0;
        }}
        p {{
            font-size: 1.1em;
            color: #e0e0e0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .image-container {{
            background: #2d2d2d;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}
        .image-path {{
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            color: #a0a0a0;
            background: #363636;
            border-radius: 4px;
        }}
        .debug-info {{
            background: #2d2d2d;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            color: #e0e0e0;
            border: 1px solid #404040;
            border-radius: 8px;
        }}
        ul {{
            list-style-type: none;
        }}
        li {{
            color: #e0e0e0;
        }}
        .buttons {{
            display: flex;
            gap: 1em;
        }}
        .buttons a {{
            text-decoration: none;
        }}
        .buttons button {{
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        section {{
            background: #2d2d2d;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            padding: 1em;
        }}
        .body-text {{
            color: #e0e0e0;
            font-size: 1.1em;
        }}
        .section-text {{
            color: #e0e0e0;
            font-size: 1.1em;
        }}
        .div-text {{
            color: #e0e0e0;
            font-size: 1.1em;
        }}
        .error-container {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background-color: #2d2d2d;
            border-top: 2px solid #404040;
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        }}
        .error-title {{
            color: #ff6b6b;
            font-weight: 600;
            font-size: 1.1em;
        }}
        .error-message {{
            font-family: 'Consolas', monospace;
            white-space: pre-wrap;
            color: #ff8787;
            background-color: #363636;
            border-radius: 8px;
            font-size: 0.95em;
        }}
    </style>
</head>
<body{style_dict_to_html(body_style)}>"""]
        
        if body_text:
            html_parts.append(f'<div class="body-text">{body_text}</div>')
        
        if "body" in data:
            body = data["body"]
            if "children" in body:
                for child in body["children"]:
                    html_parts.append(render_component(child))
        
        html_parts.append("</body>\n</html>")
        return "\n".join(html_parts), True

    except yaml.YAMLError as e:
        error_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YAML Error</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.6;
        }}
        .error-container {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            margin: 0;
            padding: 1.2em;
            background-color: #2d2d2d;
            border-top: 2px solid #404040;
            z-index: 1000;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        }}
        .error-title {{
            color: #ff6b6b;
            font-weight: 600;
            margin-bottom: 0.8em;
            font-size: 1.1em;
        }}
        .error-message {{
            font-family: 'Consolas', monospace;
            white-space: pre-wrap;
            color: #ff8787;
            background-color: #363636;
            padding: 1em;
            border-radius: 8px;
            margin-top: 0.5em;
            font-size: 0.95em;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-title">YAML Error</div>
        <div class="error-message">{str(e)}</div>
    </div>
</body>
</html>"""
        return error_html, False 