import json
import argparse
import logging
import toml
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger("tools_generator")


def generate_tools_from_openapi(app) -> List[Dict[str, Any]]:
    """Extract all endpoints from FastAPI app and convert to tool format."""

    logger.debug("Generating tools from OpenAPI specification...")

    from fastapi.openapi.utils import get_openapi

    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Store schemas/components for resolving $ref
    components = openapi_schema.get("components", {})
    schemas = components.get("schemas", {})

    # Create the tools list
    tools = []

    # Iterate over paths
    for path, path_item in openapi_schema.get("paths", {}).items():
        # Iterate over methods
        for method, operation in path_item.items():

            # Skip non-HTTP methods
            if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                continue

            # Skip utility endpoints
            if any(skip in path for skip in ["/health", "/docs", "/redoc", "/openapi.json"]):
                continue

            # Build tool definition
            tool = {
                # Define the tool's name based on operationId, method and path
                "name": operation.get(
                    "operationId", f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
                ),
                # Use summary or description for tool description
                "description": operation.get("summary") or operation.get("description", "No description available"),
                # HTTP method
                "method": method.upper(),
                # API path
                "path": path,
                # Parameters, request body, responses, security, tags
                "parameters": extract_parameters(operation, schemas),
                "request_body": extract_request_body(operation, schemas),
                "responses": extract_responses(operation, schemas),
                "security": operation.get("security", []),
                "tags": operation.get("tags", []),
            }

            # Append tool to the list
            tools.append(tool)

    logger.debug("Tools generation completed.")

    return tools


def extract_parameters(operation: Dict, schemas: Dict) -> List[Dict[str, Any]]:
    """Extract path, query, and header parameters."""

    logger.debug("Extracting parameters...")

    # Initialize parameters list
    params = []

    # Iterate over parameters
    for param in operation.get("parameters", []):
        param_schema = param.get("schema", {})

        # Resolve $ref in parameter schema
        if "$ref" in param_schema:
            param_schema = simplify_schema(param_schema, schemas)

        params.append(
            {
                "name": param.get("name"),
                "location": param.get("in"),  # path, query, header, cookie
                "type": param_schema.get("type", "string"),
                "format": param_schema.get("format"),
                "required": param.get("required", False),
                "description": param.get("description", ""),
                "default": param_schema.get("default"),
                "enum": param_schema.get("enum"),
            }
        )

    return params


def extract_request_body(operation: Dict, schemas: Dict) -> Dict[str, Any]:
    """Extract request body schema."""

    logger.debug("Extracting request body schema...")

    # Get request body
    request_body = operation.get("requestBody")
    if not request_body:
        return None

    # Extract content for application/json
    content = request_body.get("content", {})
    json_content = content.get("application/json", {})

    return {
        "required": request_body.get("required", False),
        "content_type": "application/json",
        "schema": simplify_schema(json_content.get("schema", {}), schemas),
        "description": request_body.get("description", ""),
    }


def extract_responses(operation: Dict, schemas: Dict) -> Dict[str, Any]:
    """Extract response schemas."""

    logger.debug("Extracting response schemas...")

    # Initialize responses dictionary
    responses = {}

    # Iterate over responses
    for status_code, response in operation.get("responses", {}).items():
        content = response.get("content", {})
        json_content = content.get("application/json", {})

        responses[status_code] = {
            "description": response.get("description", ""),
            "schema": simplify_schema(json_content.get("schema", {}), schemas),
        }

    return responses


def resolve_ref(ref: str, schemas: Dict) -> Dict:
    """Resolve $ref to actual schema definition."""

    logger.debug(f"Resolving reference: {ref}")

    if not ref or not ref.startswith("#/components/schemas/"):
        return {}

    schema_name = ref.split("/")[-1]
    return schemas.get(schema_name, {})


def simplify_schema(schema: Dict, schemas: Dict, depth: int = 0, max_depth: int = 3) -> Dict:
    """
    Simplify OpenAPI schema by resolving $ref and nested structures.
    """

    logger.debug("Simplifying schema...")

    if not schema or depth > max_depth:
        return {}

    # Resolve $ref if present
    if "$ref" in schema:
        resolved = resolve_ref(schema["$ref"], schemas)
        return simplify_schema(resolved, schemas, depth + 1, max_depth)

    simplified = {}

    # Copy basic fields
    for key in ["type", "format", "description", "example", "default", "enum", "title"]:
        if key in schema:
            simplified[key] = schema[key]

    # Handle properties (object type)
    if "properties" in schema:
        simplified["properties"] = {}
        for prop_name, prop_schema in schema["properties"].items():
            simplified["properties"][prop_name] = simplify_schema(prop_schema, schemas, depth + 1, max_depth)

    # Handle required fields
    if "required" in schema:
        simplified["required"] = schema["required"]

    # Handle arrays
    if "items" in schema:
        simplified["items"] = simplify_schema(schema["items"], schemas, depth + 1, max_depth)

    # Handle anyOf, oneOf, allOf
    for key in ["anyOf", "oneOf", "allOf"]:
        if key in schema:
            simplified[key] = [simplify_schema(s, schemas, depth + 1, max_depth) for s in schema[key]]

    return simplified


def save_tools_toml(tools: List[Dict], output_dir: Path):
    """Save tools to TOML format (most compact for LLMs)."""

    logger.debug("Saving tools to TOML format...")

    # Create the structure data
    organized_tools = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "total_tools": len(tools),
            "format": "IAM Service Tool Definitions",
        },
        "tools": tools,
    }

    # Create output file path
    output_file = output_dir / "iam_tools.toml"

    # Write to TOML file
    with open(output_file, "w", encoding="utf-8") as f:
        toml.dump(organized_tools, f)

    logger.info(f"Generated TOML → {output_file} ({len(tools)} tools)")

    return output_file


def save_tools_json(tools: List[Dict], output_dir: Path):
    """Save tools to JSON format (universal compatibility)."""

    logger.debug("Saving tools to JSON format...")

    # Create the structure data
    organized_tools = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "total_tools": len(tools),
            "format": "IAM Service Tool Definitions",
        },
        "tools": tools,
    }

    # Create output file path
    output_file = output_dir / "iam_tools.json"

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(organized_tools, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated JSON → {output_file} ({len(tools)} tools)")
    return output_file


def save_tools_yaml(tools: List[Dict], output_dir: Path):
    """Save tools to YAML format."""

    logger.debug("Saving tools to YAML format...")

    # Create the structure data
    organized_tools = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "total_tools": len(tools),
            "format": "IAM Service Tool Definitions",
        },
        "tools": tools,
    }

    # Create output file path
    output_file = output_dir / "iam_tools.yaml"

    # Write to YAML file
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(organized_tools, f, default_flow_style=False, allow_unicode=True)

    logger.info(f"Generated YAML → {output_file} ({len(tools)} tools)")
    return output_file


def generate_mcp_format(tools: List[Dict], output_dir: Path):
    """
    Generate tools in Anthropic MCP (Model Context Protocol) format.
    Compatible with Claude Desktop and other MCP clients.
    """

    logger.debug("Generating tools in Anthropic MCP format...")

    mcp_tools = []

    for tool in tools:

        # Create the structure data
        mcp_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }

        # Add path/query parameters
        for param in tool.get("parameters", []):
            mcp_tool["input_schema"]["properties"][param["name"]] = {
                "type": param["type"],
                "description": param.get("description", ""),
            }

            if param.get("enum"):
                mcp_tool["input_schema"]["properties"][param["name"]]["enum"] = param["enum"]

            if param.get("required"):
                mcp_tool["input_schema"]["required"].append(param["name"])

        # Add request body fields
        request_body = tool.get("request_body")
        if request_body and request_body.get("schema"):
            body_schema = request_body["schema"]
            props = body_schema.get("properties", {})

            for prop_name, prop_schema in props.items():
                mcp_tool["input_schema"]["properties"][prop_name] = prop_schema

            # Add required fields from body
            body_required = body_schema.get("required", [])
            mcp_tool["input_schema"]["required"].extend(body_required)

        mcp_tools.append(mcp_tool)

    # Write to MCP JSON file
    output_file = output_dir / "iam_tools_mcp.json"

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"tools": mcp_tools}, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated MCP format → {output_file} ({len(mcp_tools)} tools)")
    return output_file


def generate_langchain_format(tools: List[Dict], output_dir: Path):
    """
    Generate tools in LangChain-compatible format.
    Can be used with Ollama, OpenAI, Anthropic, etc.
    """

    logger.debug("Generating tools in LangChain format...")

    langchain_tools = []

    for tool in tools:

        # Create the structure data
        lc_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "api_method": tool["method"],
            "api_path": tool["path"],
            "parameters": {},
        }

        # Combine all parameters into flat structure
        for param in tool.get("parameters", []):
            lc_tool["parameters"][param["name"]] = {
                "type": param["type"],
                "description": param.get("description", ""),
                "required": param.get("required", False),
                "location": param.get("location", "query"),
            }

        # Add request body as parameters
        request_body = tool.get("request_body")
        if request_body and request_body.get("schema"):
            body_props = request_body["schema"].get("properties", {})
            body_required = request_body["schema"].get("required", [])

            for prop_name, prop_schema in body_props.items():
                lc_tool["parameters"][prop_name] = {
                    "type": prop_schema.get("type", "string"),
                    "description": prop_schema.get("description", ""),
                    "required": prop_name in body_required,
                    "location": "body",
                }

        langchain_tools.append(lc_tool)

    # Write to LangChain JSON file
    output_file = output_dir / "iam_tools_langchain.json"

    # Write to JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"tools": langchain_tools}, f, indent=2, ensure_ascii=False)

    logger.info(f"Generated LangChain format → {output_file} ({len(langchain_tools)} tools)")
    return output_file


def main():
    """Main function to generate tool definitions from FastAPI OpenAPI spec."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate AI agent tools from FastAPI OpenAPI spec")

    # Add format argument when calling the script, to specify output file format
    parser.add_argument(
        "--format",
        choices=["toml", "json", "yaml", "mcp", "langchain", "all"],
        default="all",
        help="Output format (default: all)",
    )
    # Add output directory argument when calling the script, to specify output directory
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tools"),
        help="Output directory (default: tools)",
    )

    args = parser.parse_args()

    # Import app
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.main import app

    logger.info("Extracting tools from FastAPI OpenAPI specification...")
    tools = generate_tools_from_openapi(app)
    logger.info(f"Found {len(tools)} API endpoints")

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Generate requested formats
    logger.info(f"Generating tool definitions in {args.format} format(s)...")

    if args.format in ["toml", "all"]:
        save_tools_toml(tools, args.output)

    if args.format in ["json", "all"]:
        save_tools_json(tools, args.output)

    if args.format in ["yaml", "all"]:
        save_tools_yaml(tools, args.output)

    if args.format in ["mcp", "all"]:
        generate_mcp_format(tools, args.output)

    if args.format in ["langchain", "all"]:
        generate_langchain_format(tools, args.output)

    logger.info("Successfully generated tool definitions!")


if __name__ == "__main__":
    main()
