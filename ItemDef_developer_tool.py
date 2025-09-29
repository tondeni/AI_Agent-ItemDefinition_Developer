# tool.py
import json
import os
from datetime import datetime
from cat.mad_hatter.decorators import tool
from cat.log import log

# Path to templates
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "item_definition_iso26262.json")
GUIDANCE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "item_definition_template_guidance.json")

@tool(return_direct=True)
def generate_iso_26262_item_definition(tool_input, cat):
    """
    Generate a structured, ISO 26262-3:2018 compliant Item Definition for an automotive system.
    This creates a COMPLETE item definition with LLM-generated content for a specific system.

    Use this tool when the user asks to:
    - "Generate item definition for [system name]"
    - "Create ISO 26262 item definition for [system]"
    - "Develop item definition for [system]"

    - You are acting as a certified Functional Safety Engineer (ISO 26262).
    - Use formal, precise, technical language. Avoid casual tone, humor, metaphors, or jokes.
    - Use an impersonal professional language. Make the item the main subject of the document
    - Focus on clarity, traceability, and completeness – as required by functional safety standards.
    - Structure content logically: define scope, interfaces, modes, constraints, and safety-related assumptions.
    - Use passive voice where appropriate (e.g., "The system shall...", "It is assumed that...").
    - Prioritize unambiguous terminology (e.g., "The BMS shall monitor cell voltage" not "The BMS watches the battery").
    - If uncertain, state assumptions explicitly rather than guessing.

    Expected tool_input format (JSON string or dict):
        {
            "system_name": "Battery Management System",
            "system_id": "BMS-EV23",
            "focus_section": "interfaces"  # optional
        }
    If tool_input is string, tries to parse as JSON. Otherwise, uses defaults.
    """
    
    print("✅ TOOL CALLED: generate_iso_26262_item_definition")
    
    # Default values
    system_name = "Unknown System"
    system_id = ""
    focus_section = None

    # Parse tool_input
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            # If not valid JSON, treat as system_name
            system_name = tool_input.strip()
    if isinstance(tool_input, dict):
        system_name = tool_input.get("system_name", system_name)
        system_id = tool_input.get("system_id", system_id)
        focus_section = tool_input.get("focus_section", focus_section)

    # Load template
    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = json.load(f)
    except Exception as e:
        log.error(f"Failed to load template: {e}")
        return "❌ Error: Could not load Item Definition template."

    # Personalize metadata
    now_str = datetime.now().strftime("%Y-%m-%d")
    template["metadata"]["generated_date"] = now_str
    template["system_info"]["item_name"] = system_name
    template["system_info"]["item_id"] = system_id or f"{system_name.upper().replace(' ', '_')}_DEFAULT"
    template["system_info"]["description"] = f"The {system_name} is a critical automotive system responsible for..."

    # Adjust weights if focus_section is provided
    if focus_section:
        focus_section = focus_section.lower()
        boosted_sections = []

        # Boost top-level sections
        for sec_key in template["sections"]:
            sec_data = template["sections"][sec_key]
            title = sec_data.get("title", "").lower()
            if focus_section in sec_key.lower() or focus_section in title:
                sec_data["weight"] = 2.0
                boosted_sections.append(sec_key)

        # Boost subsections
        for sec_key, sec_data in template["sections"].items():
            if "subsections" in sec_data:
                for sub_key, sub_data in sec_data["subsections"].items():
                    sub_title = sub_data.get("title", "").lower()
                    if focus_section in sub_key.lower() or focus_section in sub_title:
                        sub_data["weight"] = 2.0
                        boosted_sections.append(f"{sec_key} -> {sub_key}")

        if not boosted_sections:
            log.warning(f"Focus section '{focus_section}' not found in template.")
        else:
            log.info(f"Boosted sections: {boosted_sections}")

    # Generate content
    output_lines = []
    output_lines.append(f"# ISO 26262 Item Definition: {system_name}")
    output_lines.append(f"*Work Product: {template['metadata']['work_product']}*")
    output_lines.append(f"*Generated on: {now_str}*")
    output_lines.append("")

    for sec_key, sec_data in template["sections"].items():
        if "title" not in sec_data:
            continue

        title = sec_data["title"]
        output_lines.append(f"## {title}")
        if "clause_ref" in sec_data:
            output_lines.append(f"*Clause: {sec_data['clause_ref']}*")

        # Handle subsections
        if "subsections" in sec_data:
            for sub_key, sub_data in sec_data["subsections"].items():
                sub_title = sub_data["title"]
                output_lines.append(f"### {sub_title}")
                if "clause_ref" in sub_data:
                    output_lines.append(f"*Clause: {sub_data['clause_ref']}*")

                # Build prompt
                prompt = sub_data["prompt"].format(
                    system_name=system_name,
                    system_id=system_id,
                    datetime_now=now_str
                )
                if sub_data.get("weight", 1.0) > 1.0:
                    prompt = f"[FOCUS AREA - IMPORTANT] {prompt}"

                try:
                    content = cat.llm(prompt)
                    sub_data["content"] = content.strip()
                    output_lines.append(content.strip())
                except Exception as e:
                    log.error(f"LLM failed for {sub_key}: {e}")
                    output_lines.append("[Content generation failed]")

                output_lines.append("")

        else:
            # Top-level section
            prompt = sec_data["prompt"].format(
                system_name=system_name,
                system_id=system_id,
                datetime_now=now_str
            )
            if sec_data.get("weight", 1.0) > 1.0:
                prompt = f"[FOCUS AREA - IMPORTANT] {prompt}"

            try:
                content = cat.llm(prompt)
                sec_data["content"] = content.strip()
                output_lines.append(content.strip())
            except Exception as e:
                log.error(f"LLM failed for {sec_key}: {e}")
                output_lines.append("[Content generation failed]")

            output_lines.append("")

    # ✅ SET WORKING MEMORY FLAG FOR FORMATTER PLUGIN
    cat.working_memory["document_type"] = "item_definition"
    cat.working_memory["system_name"] = system_name
    
    return "\n".join(output_lines)

@tool(return_direct=True)
def generate_item_definition_template(tool_input, cat):
    """
    Generate a ISO 26262 Item Definition template.

     Use this tool when the user asks to:
    - "Generate item definition template"
    - "Create ISO 26262 item definition template"
    - "Develop item definition template"

    """
    
    print("✅ TOOL CALLED: generate_item_definition_template")
    
    # Parse system name if provided
    system_name = "[Item Name]"
    if isinstance(tool_input, str) and tool_input.strip():
        system_name = tool_input.strip()
    elif isinstance(tool_input, dict):
        system_name = tool_input.get("system_name", system_name)
    
    # Load the template guidance JSON
    try:
        with open(GUIDANCE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            template = json.load(f)
    except Exception as e:
        log.error(f"Failed to load template guidance: {e}")
        return "❌ Error: Could not load Item Definition template guidance."
    
    # Build content in markdown format
    output_lines = []
    
    # Header
    now_str = datetime.now().strftime("%Y-%m-%d")
    output_lines.append(f"# ISO 26262 Item Definition: {system_name}")
    output_lines.append(f"*Work Product: {template['metadata']['work_product']}*")
    output_lines.append(f"*Generated on: {now_str}*")
    output_lines.append(f"*Document Type: {template['metadata']['document_type']}*")
    output_lines.append("")
    
    # Process each section
    for sec_key, sec_data in template["sections"].items():
        if "title" not in sec_data:
            continue
        
        # Section title
        output_lines.append(f"## {sec_data['title']}")
        if "clause_ref" in sec_data:
            output_lines.append(f"*Clause: {sec_data['clause_ref']}*")
        output_lines.append("")
        
        # Handle subsections
        if "subsections" in sec_data:
            for sub_key, sub_data in sec_data["subsections"].items():
                output_lines.append(f"### {sub_data['title']}")
                if "clause_ref" in sub_data:
                    output_lines.append(f"*Clause: {sub_data['clause_ref']}*")
                output_lines.append("")
                
                # Add guidance
                if "guidance" in sub_data:
                    output_lines.append("**Guidance:**")
                    output_lines.append(sub_data["guidance"])
                    output_lines.append("")
                
                # Add format if present
                if "format" in sub_data:
                    output_lines.append("**Format:**")
                    output_lines.append(sub_data["format"])
                    output_lines.append("")
                
                # Add examples if present
                if "examples" in sub_data:
                    output_lines.append("**Examples:**")
                    for example in sub_data["examples"]:
                        output_lines.append(f"- {example}")
                    output_lines.append("")
                
                # Add modes to consider if present
                if "modes_to_consider" in sub_data:
                    output_lines.append("**Operating Modes to Consider:**")
                    for mode in sub_data["modes_to_consider"]:
                        output_lines.append(f"- {mode}")
                    output_lines.append("")
                
                # Add categories if present - FIX HERE
                if "categories" in sub_data:
                    categories = sub_data["categories"]
                    # Check if it's a dict or list
                    if isinstance(categories, dict):
                        for cat_name, cat_items in categories.items():
                            cat_title = cat_name.replace("_", " ").title()
                            output_lines.append(f"**{cat_title}:**")
                            if isinstance(cat_items, list):
                                for item in cat_items:
                                    output_lines.append(f"- {item}")
                            else:
                                output_lines.append(str(cat_items))
                            output_lines.append("")
                    elif isinstance(categories, list):
                        output_lines.append("**Categories:**")
                        for item in categories:
                            output_lines.append(f"- {item}")
                        output_lines.append("")
                
                # Add structure if present
                if "structure" in sub_data:
                    for struct_name, struct_content in sub_data["structure"].items():
                        struct_title = struct_name.replace("_", " ").title()
                        output_lines.append(f"**{struct_title}:**")
                        output_lines.append(struct_content)
                        output_lines.append("")
                
                # Add note if present
                if "note" in sub_data:
                    output_lines.append(f"*Note: {sub_data['note']}*")
                    output_lines.append("")
                
                # Add scenarios to consider if present
                if "scenarios_to_consider" in sub_data:
                    output_lines.append("**Scenarios to Consider:**")
                    for scenario in sub_data["scenarios_to_consider"]:
                        output_lines.append(f"- {scenario}")
                    output_lines.append("")
                
                output_lines.append("---")
                output_lines.append("")
        
        else:
            # Top-level section without subsections
            if "guidance" in sec_data:
                output_lines.append("**Guidance:**")
                output_lines.append(sec_data["guidance"])
                output_lines.append("")
            
            if "example" in sec_data:
                output_lines.append("**Example:**")
                output_lines.append(sec_data["example"])
                output_lines.append("")
            
            if "roles" in sec_data:
                output_lines.append("**Approval Roles:**")
                for role in sec_data["roles"]:
                    output_lines.append(f"- {role}: ____________ (Signature) ________ (Date)")
                output_lines.append("")
            
            if "configuration_items" in sec_data:
                output_lines.append("**Configuration Management:**")
                for item in sec_data["configuration_items"]:
                    output_lines.append(f"- {item}")
                output_lines.append("")
            
            output_lines.append("---")
            output_lines.append("")
    
    # Set working memory flags for formatter
    cat.working_memory["document_type"] = "item_definition"
    cat.working_memory["system_name"] = system_name
    cat.working_memory["is_template"] = True
    
    return "\n".join(output_lines)