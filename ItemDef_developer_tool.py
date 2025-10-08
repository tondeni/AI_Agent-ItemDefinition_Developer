# tool.py
import json
import os
from datetime import datetime
from cat.mad_hatter.decorators import tool
from cat.log import log

# Path to templates
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "item_definition_iso26262.json")
GUIDANCE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "item_definition_template_guidance.json")

# Helper functions
def parse_tool_input(tool_input, default_name="[Item Name]"):
    """
    Parse tool input consistently handling both JSON and plain string formats.
    
    Args:
        tool_input: String input from LLM (JSON or plain text)
        default_name: Default system_name if input is empty
        
    Returns:
        dict: Parsed parameters with at least 'system_name'
    """
    if not tool_input or (isinstance(tool_input, str) and tool_input.strip() == ""):
        return {"system_name": default_name}
    
    # Try parsing as JSON
    if isinstance(tool_input, str) and tool_input.strip().startswith('{'):
        try:
            parsed = json.loads(tool_input)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            log.warning(f"Failed to parse JSON input: {tool_input}")
    
    # Treat as plain system name
    if isinstance(tool_input, str):
        return {"system_name": tool_input.strip()}
    
    # Fallback
    return {"system_name": default_name}

def format_error_message(error_type, details=""):
    """Format consistent error messages for tools."""
    error_messages = {
        "template_not_found": "❌ Template file not found. Please verify plugin installation.",
        "template_corrupt": "❌ Template file is corrupted. Please reinstall the plugin.",
        "llm_failed": "❌ Content generation failed. Please try again.",
        "invalid_input": f"❌ Invalid input format. {details}"
    }
    return error_messages.get(error_type, f"❌ Error: {details}")

# Tools
@tool(
    return_direct=True,
    examples=[
        "generate item definition for Battery Management System",
        "create item definition for Brake System",
        "develop ISO 26262 item definition for Steering Control Unit"
    ]
)
def generate_item_definition(tool_input, cat):
    """Generate ISO 26262 Item Definition document for automotive system.
    Input: system_name (e.g. 'Battery Management System') or JSON with 'system_name', 'system_id', 'focus_section'.
    Returns complete work product per ISO 26262-3 Clause 5."""
    
    log.info("🔧 TOOL CALLED: generate_item_definition")
    
    # Parse input
    params = parse_tool_input(tool_input, default_name="Unknown System")
    system_name = params.get("system_name", "Unknown System")
    system_id = params.get("system_id", "")
    focus_section = params.get("focus_section")
    
    log.info(f"📋 Generating Item Definition for: {system_name}")
    
    # Load template
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = json.load(f)
    except FileNotFoundError:
        log.error(f"Template not found: {TEMPLATE_PATH}")
        return "❌ Error: Template file not found. Please check plugin installation."
    except json.JSONDecodeError as e:
        log.error(f"Invalid template JSON: {e}")
        return "❌ Error: Template file is corrupted."
    except Exception as e:
        log.error(f"Failed to load template: {e}")
        return "❌ Error: Could not load Item Definition template."
    
    # Apply focus weights if specified
    if focus_section:
        boosted_sections = []
        for sec_key, sec_data in template.get("sections", {}).items():
            if focus_section.lower() in sec_key.lower():
                sec_data["weight"] = sec_data.get("weight", 1.0) * 2.0
                boosted_sections.append(sec_key)
            
            # Check subsections
            if "subsections" in sec_data:
                for sub_key, sub_data in sec_data["subsections"].items():
                    if focus_section.lower() in sub_key.lower():
                        sub_data["weight"] = sub_data.get("weight", 1.0) * 2.0
                        boosted_sections.append(f"{sec_key}.{sub_key}")
        
        if boosted_sections:
            log.info(f"🎯 Focus sections boosted: {boosted_sections}")
    
    # Generate content
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output_lines = [
        f"# ISO 26262 Item Definition: {system_name}",
        f"*Work Product: {template.get('metadata', {}).get('work_product', 'Item Definition')}*",
        f"*Generated: {now_str}*",
        ""
    ]
    
    # Process sections
    for sec_key, sec_data in template.get("sections", {}).items():
        if "title" not in sec_data:
            continue
        
        title = sec_data["title"]
        output_lines.append(f"## {title}")
        
        if "clause_ref" in sec_data:
            output_lines.append(f"*Reference: {sec_data['clause_ref']}*")
        
        # Handle subsections
        if "subsections" in sec_data:
            for sub_key, sub_data in sec_data["subsections"].items():
                sub_title = sub_data.get("title", "")
                output_lines.append(f"### {sub_title}")
                
                if "clause_ref" in sub_data:
                    output_lines.append(f"*Reference: {sub_data['clause_ref']}*")
                
                # Build LLM prompt
                prompt_template = sub_data.get("prompt", "")
                prompt = prompt_template.format(
                    system_name=system_name,
                    system_id=system_id,
                    datetime_now=now_str
                )
                
                # Add focus marker if weighted
                if sub_data.get("weight", 1.0) > 1.5:
                    prompt = f"[HIGH PRIORITY SECTION] {prompt}"
                
                # Generate content
                try:
                    content = cat.llm(prompt)
                    sub_data["content"] = content.strip()
                    output_lines.append(content.strip())
                except Exception as e:
                    log.error(f"LLM generation failed for {sub_key}: {e}")
                    output_lines.append("[⚠️ Content generation failed - please regenerate]")
                
                output_lines.append("")
        
        else:
            # Top-level section without subsections
            prompt_template = sec_data.get("prompt", "")
            prompt = prompt_template.format(
                system_name=system_name,
                system_id=system_id,
                datetime_now=now_str
            )
            
            if sec_data.get("weight", 1.0) > 1.5:
                prompt = f"[HIGH PRIORITY SECTION] {prompt}"
            
            try:
                content = cat.llm(prompt)
                sec_data["content"] = content.strip()
                output_lines.append(content.strip())
            except Exception as e:
                log.error(f"LLM generation failed for {sec_key}: {e}")
                output_lines.append("[⚠️ Content generation failed - please regenerate]")
            
            output_lines.append("")
    
    # Store in working memory for other plugins
    generated_content = "\n".join(output_lines)
    cat.working_memory["item_definition_content"] = generated_content
    cat.working_memory["document_type"] = "item_definition"
    cat.working_memory["system_name"] = system_name
    
    log.info(f"✅ Item Definition generated: {len(generated_content)} characters")
    
    return generated_content

@tool(
    return_direct=True,
    examples=[
        "show item definition template",
        "give me ISO 26262 template",
        "create an item definition template"
    ]
)
def get_item_template(tool_input, cat):
    """Get ISO 26262 Item Definition template with guidance and examples.
    Input: optional system_name for placeholder (defaults to '[Item Name]').
    Returns template structure with guidance notes per ISO 26262-3."""
    
    log.info("🔧 TOOL CALLED: get_item_template")
    
    # Parse system name
    params = parse_tool_input(tool_input, default_name="[Item Name]")
    system_name = params.get("system_name", "[Item Name]")
    
    log.info(f"📋 Generating template for: {system_name}")
    
    # Load guidance template
    try:
        with open(GUIDANCE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = json.load(f)
    except FileNotFoundError:
        log.error(f"Guidance template not found: {GUIDANCE_TEMPLATE_PATH}")
        return "❌ Error: Template guidance file not found."
    except json.JSONDecodeError as e:
        log.error(f"Invalid guidance template JSON: {e}")
        return "❌ Error: Template guidance file is corrupted."
    except Exception as e:
        log.error(f"Failed to load guidance template: {e}")
        return "❌ Error: Could not load template guidance."
    
    # Build template output
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output_lines = [
        f"# ISO 26262 Item Definition Template",
        f"*System: {system_name}*",
        f"*Document Type: TEMPLATE WITH GUIDANCE*",
        f"*Generated: {now_str}*",
        "",
        "---",
        ""
    ]
    
    # Process template sections
    for sec_key, sec_data in template.get("sections", {}).items():
        if "title" not in sec_data:
            continue
        
        title = sec_data["title"]
        output_lines.append(f"## {title}")
        
        if "clause_ref" in sec_data:
            output_lines.append(f"*Reference: {sec_data['clause_ref']}*")
            output_lines.append("")
        
        # Add guidance if present
        if "guidance" in sec_data:
            output_lines.append("**Guidance:**")
            output_lines.append(sec_data["guidance"])
            output_lines.append("")
        
        # Handle subsections
        if "subsections" in sec_data:
            for sub_key, sub_data in sec_data["subsections"].items():
                sub_title = sub_data.get("title", "")
                output_lines.append(f"### {sub_title}")
                
                if "clause_ref" in sub_data:
                    output_lines.append(f"*Reference: {sub_data['clause_ref']}*")
                    output_lines.append("")
                
                # Add guidance
                if "guidance" in sub_data:
                    output_lines.append("**Guidance:**")
                    output_lines.append(sub_data["guidance"])
                    output_lines.append("")
                
                # Add format instructions
                if "format" in sub_data:
                    output_lines.append("**Format:**")
                    output_lines.append(sub_data["format"])
                    output_lines.append("")
                
                # Add examples
                if "examples" in sub_data:
                    output_lines.append("**Examples:**")
                    for example in sub_data["examples"]:
                        output_lines.append(f"  • {example}")
                    output_lines.append("")
                
                # Add operating modes
                if "modes_to_consider" in sub_data:
                    output_lines.append("**Operating Modes:**")
                    for mode in sub_data["modes_to_consider"]:
                        output_lines.append(f"  • {mode}")
                    output_lines.append("")
                
                # Add categories
                if "categories" in sub_data:
                    categories = sub_data["categories"]
                    if isinstance(categories, dict):
                        for cat_name, cat_items in categories.items():
                            cat_title = cat_name.replace("_", " ").title()
                            output_lines.append(f"**{cat_title}:**")
                            if isinstance(cat_items, list):
                                for item in cat_items:
                                    output_lines.append(f"  • {item}")
                            output_lines.append("")
                
                output_lines.append("---")
                output_lines.append("")
        
        else:
            # Top-level section guidance
            if "guidance" in sec_data:
                output_lines.append("**Guidance:**")
                output_lines.append(sec_data["guidance"])
                output_lines.append("")
            
            if "example" in sec_data:
                output_lines.append("**Example:**")
                output_lines.append(sec_data["example"])
                output_lines.append("")
            
            output_lines.append("---")
            output_lines.append("")
    
    # Store in working memory
    generated_content = "\n".join(output_lines)
    cat.working_memory["item_definition_content"] = generated_content
    cat.working_memory["document_type"] = "item_definition"
    cat.working_memory["system_name"] = system_name
    cat.working_memory["is_template"] = True
    
    log.info(f"✅ Template generated: {len(generated_content)} characters")
    
    return generated_content