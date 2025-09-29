# tool.py
import json
import os
from datetime import datetime
from cat.mad_hatter.decorators import tool
from cat.log import log

# Path to template
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "item_definition_iso26262.json")

@tool(return_direct=True)
def generate_iso_26262_item_definition(tool_input, cat):
    """
    Generate a structured, ISO 26262-3:2018 compliant Item Definition for an automotive system.

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
    
    print("✅✅✅✅✅✅✅✅ TOOL CALLED: DEVELOP ITEM DEFINITION TEMPLATE ✅✅✅✅✅✅✅✅✅✅✅")
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