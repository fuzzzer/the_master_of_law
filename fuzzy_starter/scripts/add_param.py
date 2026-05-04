#!/usr/bin/env python3

import argparse
import re
import sys
import os

"""
A Python script to add a new Dart parameter (field, constructors, copyWith,
lerp, toString, operator==, hashCode) with multi-line formatting.
It preserves 'const' if present before constructors.

Refinements:
- Named constructors that use a bracketed style: e.g. `const UiColors.dark({ ... });`
- Lerp method that has a signature like:
    @override
    ThemeExtension<UiColors> lerp(ThemeExtension<UiColors>? other, double t) {...}
  and returns `UiColors(...)`.


run:

python3 add_param.py \
  --file <full_file_path> \
  --class ClassName \
  --name newParameterName \
  --type double \
  --default-value 0.0

example:
python3 add_param.py \
  --file /Users/fuzzzer/programming/nexus/super_app_workspace/ui_kit/lib/src/themes/theme_extensions/ui_style/ui_form_styles.dart \
  --class UiFormStyles \
  --name newStyleParameter \
  --type double \
  --default-value 0.0
"""

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the Dart file")
    parser.add_argument("--class", dest="class_name", required=True, help="Name of the Dart class")
    parser.add_argument("--name", dest="param_name", required=True, help="New parameter name")
    parser.add_argument("--type", dest="param_type", required=True, help="Type of the new parameter (e.g. double)")
    parser.add_argument("--default-value", dest="default_value", default="0.0",
                        help="Default value for named constructors, etc.")
    return parser.parse_args()


# ------------------------------------------------------------------------------
# 1) Field
# ------------------------------------------------------------------------------
def ensure_field_declaration(code, class_name, param_name, param_type):
    """
    Insert `final <type> <param_name>;` in the class body if not present.
    """
    class_pattern = re.compile(
        rf"(class\s+{re.escape(class_name)}\s*.*?\{{)(.*?)(\n\}})",
        re.DOTALL
    )
    match = class_pattern.search(code)
    if not match:
        return code

    class_body = match.group(2)
    # If field is already present, skip
    field_regex = re.compile(rf"\bfinal\s+{re.escape(param_type)}\s+{re.escape(param_name)}\s*;")
    if field_regex.search(class_body):
        return code

    insertion = f"  final {param_type} {param_name};\n"
    finals = re.findall(r"(final\s+.*?;)", class_body)
    if finals:
        last_final = finals[-1]
        replacement = last_final + "\n" + insertion.rstrip()
        class_body = class_body.replace(last_final, replacement)
    else:
        class_body = insertion + class_body

    start_body = match.start(2)
    end_body = match.end(2)
    return code[:start_body] + class_body + code[end_body:]


# ------------------------------------------------------------------------------
# 2) Main constructor
# ------------------------------------------------------------------------------
def ensure_main_constructor(code, class_name, param_name, param_type):
    """
    Matches `const ClassName({ ... })` or `ClassName({ ... })`.
    If param is missing, add it on a new line with trailing comma.
    """
    pattern = re.compile(
        rf"(?P<const>const\s+)?"
        rf"(?P<name>{re.escape(class_name)})"
        rf"\s*\(\s*\{{"
        r"(?P<body>.*?)(?P<end>\}\)\s*;)",
        re.DOTALL
    )
    match = pattern.search(code)
    if not match:
        return code

    body_part = match.group("body")
    if re.search(rf"this\.{re.escape(param_name)}\b", body_part):
        return code

    is_nullable = "?" in param_type
    required_str = "" if is_nullable else "required "
    insertion = f"\n    {required_str}this.{param_name},\n"

    trimmed_body = body_part.rstrip()
    if not trimmed_body.endswith(","):
        trimmed_body += ","
    new_body = trimmed_body + insertion

    const_part = match.group("const") or ""
    start_part = match.group("name")
    end_part = match.group("end")

    replaced = const_part + start_part + "(" + "{" + new_body + end_part
    return code[:match.start()] + replaced + code[match.end():]


# ------------------------------------------------------------------------------
# 3) Named constructors (for bracket style)
# ------------------------------------------------------------------------------
def ensure_named_constructors(code, class_name, param_name, default_value):
    """
    Updates named constructors of two forms:

    1) Colon style:
         const ClassName.someName()
             : fieldA = ...,
               fieldB = ...,
               ...
               ;
       Insert ' newParam = <defaultValue>' on its own line at the end.

    2) Bracket style:
         const ClassName.someName({
           this.fieldA = ...,
           ...
         });
       Insert 'this.newParam = <defaultValue>' on its own line if missing.

    We do NOT remove `const` if it’s there; we keep it.
    """

    new_code = code

    # ------------------------------------------------------------
    # 1) COLON-STYLE Pattern
    #
    # e.g.:
    #   const ClassName.offGiga()
    #       : fieldA = ...,
    #         fieldB = ...,
    #         ...
    #         ;
    #
    # Regex approach:
    #   (?:const\s+)? => optional 'const'
    #   (ClassName\.\w+) => named constructor (e.g. ClassName.offGiga)
    #   \(\)\s*:\s* => the parentheses, then a colon
    #   ([^;]+) => body until semicolon
    #   ; => final semicolon
    #
    import re

    colon_pattern = re.compile(
        rf"(?P<const>const\s+)?(?P<ctor>{class_name}\.\w+)\s*\(\)\s*:\s*"
        r"(?P<body>[^;]+)(?P<semi>;)",
        re.DOTALL
    )
    matches_colon = list(colon_pattern.finditer(new_code))
    for match in reversed(matches_colon):
        const_part = match.group("const") or ""
        ctor_name = match.group("ctor")           # e.g. UiFormStyles.offGiga
        body_part = match.group("body")           # e.g. fieldA = 123, fieldB = 234
        semi_part = match.group("semi")           # ;

        # If paramName is already present
        if re.search(rf"{param_name}\s*=", body_part):
            continue

        # Insert at the end on a new line:
        # e.g.:  ,
        #        newParam = defaultValue
        insertion = f",\n        {param_name} = {default_value}"
        new_body = body_part.rstrip() + insertion

        replaced = f"{const_part}{ctor_name}()\n        : {new_body}{semi_part}"

        start_idx, end_idx = match.start(), match.end()
        new_code = new_code[:start_idx] + replaced + new_code[end_idx:]

    # ------------------------------------------------------------
    # 2) BRACKET-STYLE Pattern
    #
    # e.g.:
    #   const ClassName.dark({
    #     this.fieldA = ...,
    #     ...
    #   });
    #
    # Regex approach:
    #   (?:const\s+)? => optional const
    #   (ClassName\.\w+) => e.g. ClassName.dark
    #   \( => open paren
    #   \s*\{ => bracket
    #   (.*?) => capture body
    #   \}\)\s*; => close braces + semicolon
    #
    bracket_pattern = re.compile(
        rf"(?P<const>const\s+)?(?P<ctor>{class_name}\.\w+)\s*\(\s*\{{"
        r"(?P<body>.*?)(?P<end>\}\)\s*;)",
        re.DOTALL
    )
    matches_bracket = list(bracket_pattern.finditer(new_code))
    for match in reversed(matches_bracket):
        const_part = match.group("const") or ""
        ctor_name = match.group("ctor")   # e.g. UiColors.dark
        body_block = match.group("body")  # e.g. "this.fieldA =..., this.fieldB =..."
        ending = match.group("end")       # e.g. "});"

        # If we see "this.paramName"
        if re.search(rf"this\.{param_name}\b", body_block):
            continue

        # We'll insert e.g.:
        #    this.newParam = defaultValue,
        # on a new line
        insertion = f"\n    this.{param_name} = {default_value},\n"
        trimmed_body = body_block.rstrip()
        # ensure trailing comma if not present
        if not trimmed_body.endswith(","):
            trimmed_body += ","
        new_body = trimmed_body + insertion

        replaced = f"{const_part}{ctor_name}({{{new_body}{ending}"

        start_idx, end_idx = match.start(), match.end()
        new_code = new_code[:start_idx] + replaced + new_code[end_idx:]

    return new_code



# ------------------------------------------------------------------------------
# 4 copyWith
# ------------------------------------------------------------------------------
def ensure_copy_with(code, class_name, param_name, param_type):
    """
    Insert param in both signature + return call with multi-line/trailing commas.
    """
    sig_pattern = re.compile(
        rf"(?:@override\s+)?{re.escape(class_name)}\s+copyWith\s*\(\s*\{{\s*(.*?)\s*\}}\)\s*\{{",
        re.DOTALL
    )
    sig_match = sig_pattern.search(code)
    if not sig_match:
        return code

    sig_params = sig_match.group(1)
    # If param not in signature, add it
    if not re.search(rf"{re.escape(param_name)}\s*\??\s*,", sig_params):
        insertion = f"\n    {param_type}? {param_name},"
        trimmed = sig_params.rstrip()
        if not trimmed.endswith(","):
            trimmed += ","
        new_sig_block = trimmed + insertion
        old_sig_text = sig_match.group(0)
        updated_sig_text = old_sig_text.replace(sig_match.group(1), new_sig_block)
        code = code[:sig_match.start()] + updated_sig_text + code[sig_match.end():]

    # Then the return constructor
    ret_pattern = re.compile(
        rf"(return\s+{re.escape(class_name)}\s*\(\s*\{{?\s*)(.*?)(\)\s*;)",
        re.DOTALL
    )
    ret_match = ret_pattern.search(code, sig_match.start())
    if not ret_match:
        return code

    ret_params = ret_match.group(2)
    if not re.search(rf"{re.escape(param_name)}\s*:", ret_params):
        insertion_body = f"\n      {param_name}: {param_name} ?? this.{param_name},"
        ret_trim = ret_params.rstrip()
        if not ret_trim.endswith(","):
            ret_trim += ","
        new_ret_block = ret_trim + insertion_body + "\n    "
        replaced_ret = ret_match.group(1) + new_ret_block + ret_match.group(3)
        code = code[:ret_match.start()] + replaced_ret + code[ret_match.end():]

    return code


# ------------------------------------------------------------------------------
# 5) lerp
# ------------------------------------------------------------------------------
def ensure_lerp(code, class_name, param_name, param_type):
    """
    Locate the lerp method within the specified class and insert the new parameter
    into the return statement if missing. Handles different return types and parameter types.
    """
    import re


    # Corrected regex pattern to capture the entire lerp method body using a greedy match
    lerp_method_pattern = re.compile(
        rf"""@override\s+                             # Match '@override' annotation
            [\w<>,\s]+\s+                             # Match return type, e.g., ThemeExtension<UiColors>
            lerp\s*                                   # Match method name 'lerp'
            \(\s*ThemeExtension<{re.escape(class_name)}>\?\s+\w+,\s*double\s+\w+\s*\)\s*  # Match parameters
            \{{                                       # Match opening brace
            (?P<method_body>.*)                       # Capture method body greedily
            \}}                                       # Match closing brace
        """,
        re.DOTALL | re.VERBOSE
    )

    # Debug: Log the regex pattern

    # Find the lerp method
    method_match = lerp_method_pattern.search(code)
    if not method_match:
        return code  # No lerp method found, return the original code

    method_body = method_match.group("method_body")

    # Regex to find the 'return UiColors(' statement
    return_pattern = re.compile(
        rf"return\s+{re.escape(class_name)}\s*\(\s*",  # Match 'return UiColors(' with optional spaces
        re.MULTILINE
    )

    return_match = return_pattern.search(method_body)
    if not return_match:
        return code  # No return statement found, return the original code

    # Find the position of the opening parenthesis after 'return UiColors'
    start_index = return_match.end()

    # Now, find the closing ');' from the start_index
    closing_pattern = re.compile(r"\);\s*$", re.MULTILINE)
    closing_match = closing_pattern.search(method_body, pos=start_index)
    if not closing_match:
        return code  # No closing found, return original code

    # Extract the parameters string
    params_str = method_body[start_index:closing_match.start()]

    # Check if the parameter already exists
    param_pattern = re.compile(rf"{re.escape(param_name)}\s*:")
    if param_pattern.search(params_str):
        return code  # Parameter already exists, return the original code

    # Decide insertion based on param_type
    if param_type == "Color":
        insertion = f"Color.lerp({param_name}, other.{param_name}, t)!,"
    elif param_type.startswith("double"):
        insertion = f"lerpDouble({param_name}, other.{param_name}, t) ?? {param_name},"
    else:
        # For other types, define interpolation logic as needed
        insertion = f"t < 0.5 ? {param_name} : other.{param_name},"


    # Split existing parameters into lines
    params_lines = params_str.strip().split('\n')

    # Determine the indentation (assume the existing params have uniform indentation)
    if params_lines:
        last_param_line = params_lines[-1]
        indent_match = re.match(r"(\s*)\w+\s*:", last_param_line)
        indent = indent_match.group(1) if indent_match else "  "  # Default to 2 spaces
    else:
        indent = "  "  # Default indentation

    # Ensure the last existing parameter ends with a comma
    if params_lines and not params_lines[-1].strip().endswith(','):
        params_lines[-1] = params_lines[-1].rstrip() + ","

    # Prepare the new parameter line
    new_param_line = f"{indent}{param_name}: {insertion}"

    # Append the new parameter
    params_lines.append(new_param_line)

    # Reconstruct the parameters string
    new_params_str = "\n".join(params_lines)

    # Reconstruct the return statement
    # Get the indentation level of 'return UiColors(' line
    return_line_start = return_match.start()
    preceding_code = method_body[:return_match.start()]
    return_indent_match = re.search(r"(\s*)return\s+", preceding_code)
    return_indent = return_indent_match.group(1) if return_indent_match else ""

    # Indent the closing ');' correctly
    new_return_statement = f"return {class_name}(\n{new_params_str}\n{return_indent}  );"

    # Replace the old return statement with the new one in the method body
    updated_method_body = (
        method_body[:return_match.start()] +
        new_return_statement +
        method_body[closing_match.end():]
    )

    # Replace the method body in the original code
    start = method_match.start("method_body")
    end = method_match.end("method_body")
    new_code = code[:start] + updated_method_body + code[end:]

    return new_code


# ------------------------------------------------------------------------------
# 6) toString
# ------------------------------------------------------------------------------
def ensure_to_string(code, class_name, param_name):
    """
    Insert ', paramName: $paramName' in toString => 'ClassName(...)'
    """
    pattern = re.compile(
        rf"(?:@override\s+)?String\s+toString\s*\(\)\s*\{{(.*?)\}}",
        re.DOTALL
    )
    match = pattern.search(code)
    if not match:
        return code

    body = match.group(1)
    return_pattern = re.compile(
        rf"(return\s+['\"]{re.escape(class_name)}\((.*)\)['\"]\s*;)",
        re.DOTALL
    )
    ret_match = return_pattern.search(body)
    if not ret_match:
        return code

    inside = ret_match.group(2)
    if param_name in inside:
        return code

    insertion = f", {param_name}: ${param_name}"
    new_inside = inside.rstrip(" )")
    if new_inside.endswith(")"):
        new_inside = new_inside[:-1]
    new_inside += insertion + ")"

    replaced_return = ret_match.group(1).replace(ret_match.group(2), new_inside)
    new_body = body.replace(ret_match.group(1), replaced_return)

    start_body = match.start(1)
    end_body = match.end(1)
    return code[:start_body] + new_body + code[end_body:]


# ------------------------------------------------------------------------------
# 7) operator==
# ------------------------------------------------------------------------------
def ensure_operator_equal(code, class_name, param_name):
    """
    Insert `&& other.paramName == paramName` if missing in operator==.
    """
    op_pattern = re.compile(
        rf"(?:@override\s+)?bool\s+operator\s*==\s*\(Object\s+\w+\)\s*\{{(.*?)\}}",
        re.DOTALL
    )
    match = op_pattern.search(code)
    if not match:
        return code

    body = match.group(1)
    if param_name in body:
        return code

    pattern_line = re.compile(r"(other\.\w+\s*==\s*\w+)(?=\s*(?:&&|;))")
    lines = pattern_line.findall(body)
    if not lines:
        insertion = f" &&\n        other.{param_name} == {param_name}"
        new_body = re.sub(r";\s*$", insertion + ";", body.strip(), flags=re.MULTILINE)
    else:
        last_line = lines[-1]
        pos = body.rfind(last_line) + len(last_line)
        insertion = f" &&\n        other.{param_name} == {param_name}"
        new_body = body[:pos] + insertion + body[pos:]

    start_body = match.start(1)
    end_body = match.end(1)
    return code[:start_body] + new_body + code[end_body:]


# ------------------------------------------------------------------------------
# 8) hashCode
# ------------------------------------------------------------------------------
def ensure_hash_code(code, class_name, param_name):
    """
    Insert '^ paramName.hashCode' if missing in `get hashCode { return ...; }`.
    """
    hash_pattern = re.compile(
        rf"(?:@override\s+)?int\s+get\s+hashCode\s*\{{\s*return\s+(.*?);\s*\}}",
        re.DOTALL
    )
    match = hash_pattern.search(code)
    if not match:
        return code

    body = match.group(1).strip()
    if param_name in body:
        return code

    insertion = f" ^ {param_name}.hashCode"
    new_body = body + insertion

    start = match.start(1)
    end = match.end(1)
    return code[:start] + new_body + code[end:]


def main():
    args = parse_args()

    if not os.path.isfile(args.file):
        print(f"Error: File '{args.file}' does not exist.")
        sys.exit(1)

    with open(args.file, "r", encoding="utf-8") as f:
        original_code = f.read()

    code = original_code

    # 1) final field
    code = ensure_field_declaration(code, args.class_name, args.param_name, args.param_type)
    # 2) main constructor
    code = ensure_main_constructor(code, args.class_name, args.param_name, args.param_type)
    # 3) named constructors (bracket style)
    code = ensure_named_constructors(code, args.class_name, args.param_name, args.default_value)
    # 4) copyWith
    code = ensure_copy_with(code, args.class_name, args.param_name, args.param_type)
    # 5) lerp
    code = ensure_lerp(code, args.class_name, args.param_name, args.param_type)
    # 6) toString
    code = ensure_to_string(code, args.class_name, args.param_name)
    # 7) operator==
    code = ensure_operator_equal(code, args.class_name, args.param_name)
    # 8) hashCode
    code = ensure_hash_code(code, args.class_name, args.param_name)

    if code != original_code:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Parameter '{args.param_name}' successfully added to '{args.class_name}' in '{args.file}'.")
    else:
        print(f"No changes made. Possibly '{args.param_name}' is already present or code structure not matched.")


if __name__ == "__main__":
    main()
