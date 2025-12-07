import os
import xmlschema

def validateFile(xmlFile: str, xsdSchema: str) -> list:
    schema = xmlschema.XMLSchema(xsdSchema)
    errors = list(schema.iter_errors(xmlFile))
    if not errors:
        return [f"{xmlFile}: valid"]
    else:
        return [f"{xmlFile}: {len(errors)} errors"] + [f"   - {err}" for err in errors]
    return errors

def validateDirectory(xmlDirectory, xsdSchema) -> list:
    schema = xmlschema.XMLSchema(xsdSchema)
    result = []
    for file in os.listdir(xmlDirectory):
        print(f"Validating {file}...")
        xmlPath = os.path.join(xmlDirectory, file)
        errors = list(schema.iter_errors(xmlPath))

        if not errors:
            result.append(f"{file}: valid")
        else:
            result.append(f"{file}: {len(errors)} errors")
            for err in errors:
                result.append(f"   - {err}")
    return result
