# Item Definition Developer Plugin
**ISO 26262-3:2018, Clause 5 Compliant**

**Version:** 0.0.1  
**Author:** Tonino De Nigris  
**Repository:** https://github.com/tondeni/AI_Agent-ItemDefinition_Developer

---

## OVERVIEW

The Item Definition Developer plugin enables AI agents to develop ISO 26262-3 compliant Item Definition work products. An Item Definition describes the boundaries, interfaces, and functional behavior of an automotive system under development. This plugin automates the creation of comprehensive Item Definitions following the structure and requirements specified in ISO 26262-3:2018, Clause 5.

**Key Capabilities:**
- Generate complete Item Definition documents from system descriptions
- Create customizable Item Definition templates
- Support for both specific system definitions and generic templates
- Automatic structuring per ISO 26262-3 Clause 5 requirements
- Integration with downstream HARA Assistant plugin

**Purpose:**
The Item Definition is the foundation document for functional safety analysis. It defines what the system is, what it does, how it operates, and where its boundaries lie. This plugin ensures that all required elements are present and properly documented, enabling effective hazard analysis in subsequent safety lifecycle phases.

---

## WORKFLOW

### Internal Workflow

The Item Definition Developer follows a structured generation process:

```
User Input (System Name/Description)
    ↓
Template Loading & Validation
    ↓
Section Weight Adjustment (if focus area specified)
    ↓
Structured LLM Prompting
    ↓
Content Generation per Section
    ↓
Format & Store in Working Memory
    ↓
Output Complete Item Definition
```

### Integration with Other Plugins

**Downstream Integration:**

1. **HARA Assistant Plugin**
   - **Data Flow:** Item Definition → Function Extraction
   - **Method:** Working memory sharing or file-based
   - **Use Case:** HARA Assistant reads Item Definition to extract safety-relevant functions for HAZOP analysis
   - **Command Chain:** 
     ```
     1. "generate item definition for [System]"
     2. "extract functions from [System]"
     ```

**Workflow Position:**
```
Item Definition Developer (Phase 1)
    ↓
[Working Memory: item_definition_content]
    ↓
HARA Assistant (Phase 2)
    ↓
FSC Developer (Phase 3)
```

### Typical Usage Scenarios

**Scenario 1: New System Development**
```
1. User: "generate item definition for Battery Management System"
2. Plugin generates complete Item Definition
3. Content stored in working memory
4. User: "extract functions from Battery Management System"
5. HARA Assistant reads from working memory
```

**Scenario 2: Template Creation**
```
1. User: "create item definition template"
2. Plugin generates blank template with guidance
3. User manually fills in system-specific details
4. Save to item_definitions/ folder
```

**Scenario 3: Focused Development**
```
1. User: "generate item definition for Steering System, focus on interfaces"
2. Plugin generates definition with enhanced interface section
3. Use for integration-critical systems
```

---

## FUNCTIONALITIES

### 1. Generate Item Definition
**Description:** Creates a complete ISO 26262-3 Clause 5 compliant Item Definition for a specified automotive system. Generates all required sections including item description, operational environment, functional behavior, dependencies, and safety requirements.

**Input:**
- `system_name` (string) - Name of the automotive system (e.g., "Battery Management System", "Adaptive Cruise Control")
- `system_id` (string, optional) - System identifier code
- `focus_section` (string, optional) - Section to emphasize (e.g., "interfaces", "functions", "environment")

**Output:**
- Complete Item Definition document with all ISO 26262-3 Clause 5 sections
- Stored in working memory under key `item_definition_content`
- Document includes: item description, functions, interfaces, operational environment, constraints, assumptions, and preliminary safety requirements

---

### 2. Generate Item Definition Template
**Description:** Creates a blank Item Definition template with guidance, descriptions, and examples for each section. Useful for manual completion or as a reference structure.

**Input:**
- `system_name` (string, optional) - System name to include in template, defaults to "System Name"

**Output:**
- Structured template with empty fields and guidance for each section
- Instructions and examples for completing each element
- Formatted per ISO 26262-3 Clause 5 structure
- Stored in working memory with `is_template` flag set to true

---

### 3. Save Item Definition to File
**Description:** Saves the generated Item Definition from working memory to a file in the plugin's item_definitions/ folder for later use or integration with other plugins.

**Input:**
- Working memory content (`item_definition_content`)
- Optional filename specification

**Output:**
- Text file saved in `plugins/AI_Agent-ItemDefinition_Developer/item_definitions/`
- File format: `[SystemName]_ItemDefinition_[timestamp].txt`
- Confirmation message with file location

---

## GENERATED SECTIONS

The plugin generates the following ISO 26262-3 Clause 5 sections:

1. **Item Description** - Overview, purpose, system boundaries
2. **Functional Behavior** - Operating modes, functions, performance
3. **Interfaces** - Electrical, mechanical, communication interfaces
4. **Operational Environment** - Environmental conditions, operational situations
5. **Dependencies** - External systems, shared resources
6. **Assumptions** - Design assumptions, limitations
7. **Preliminary Safety Requirements** - Initial safety considerations

Each section includes:
- Detailed content based on system type
- Guidance notes where applicable
- ISO 26262 clause references
- Structured formatting for readability

---

## USAGE EXAMPLES

### Example 1: Generate Complete Item Definition
```
User: generate item definition for Electric Power Steering System

Output:
✅ Item Definition Generated: Electric Power Steering System

# ITEM DEFINITION
## Electric Power Steering System

### 1. Item Description
The Electric Power Steering (EPS) System provides steering assistance 
to the driver through an electric motor...

[Complete sections 1-7 generated]

---
Stored in working memory. Ready for HARA analysis.
```

### Example 2: Create Template
```
User: create item definition template

Output:
✅ Item Definition Template Generated

# ITEM DEFINITION TEMPLATE
## [System Name]

### 1. Item Description
**Guidance:** Provide a clear description of the item...
**Example:** The [System] is responsible for...

[Template structure with guidance for all sections]
```

### Example 3: Focused Generation
```
User: generate item definition for Brake-by-Wire System, focus on interfaces

Output:
✅ Item Definition Generated: Brake-by-Wire System
[Enhanced interface section with detailed descriptions]
```

---

## FILE STRUCTURE

```
AI_Agent-ItemDefinition_Developer/
├── plugin.json
├── README.md
├── ItemDef_developer_tool.py        # Main tool implementation
├── templates/
│   └── item_definition_structure.json  # ISO 26262-3 structure
├── item_definitions/                # Generated documents
└── assets/
    └── FuSa_AI_Agent_Plugin_logo.png
```

---

## ISO 26262 COMPLIANCE

This plugin implements requirements from:

- ✅ **ISO 26262-3:2018, Clause 5.4** - Item definition work product
- ✅ **ISO 26262-3:2018, Table 2** - Work product characteristics
- ✅ **ISO 26262-8:2018, Clause 6** - Configuration management

**Work Product Elements Covered:**
- Item description and boundaries
- Item's functions and operational environment
- Dependencies on other items
- Assumptions and constraints
- Preliminary architectural assumptions
- Interfaces to other systems

---

## BEST PRACTICES

1. **Be Specific:** Provide detailed system names for more accurate Item Definitions
2. **Review and Refine:** Generated content should be reviewed and refined by domain experts
3. **Use Focus:** Specify focus areas for complex systems with critical interfaces
4. **Chain Workflows:** Generate Item Definition before starting HARA analysis
5. **Version Control:** Save multiple iterations with timestamps for traceability

---

## INTEGRATION TIPS

**For HARA Assistant Integration:**
- Generate Item Definition first
- Keep content in working memory for seamless handoff
- Use exact system name in both plugins
- Verify function extraction picks up all safety-relevant functions

**For Manual Use:**
- Export Item Definition to file
- Review and edit as needed
- Place in HARA Assistant's item_definitions/ folder
- Proceed with hazard analysis

---

## LIMITATIONS

- Plugin generates content based on common automotive system patterns
- Domain-specific technical details may require expert review
- Generated content should be validated against actual system specifications
- Not a replacement for engineering analysis, but a documentation accelerator

---

## SUPPORT

**GitHub:** https://github.com/tondeni/AI_Agent-ItemDefinition_Developer  
**Issues:** Report issues via GitHub Issues  
**Author:** Tonino De Nigris

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**ISO 26262 Edition:** 2018 (2nd Edition)