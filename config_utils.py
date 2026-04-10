import tomli as tomllib
import pydantic
import pathlib


CONFIG_DIR = pathlib.Path("C:\EXP\python\Qoptics_exp\configs")

def load_settings(module_name: str, schema: pydantic.BaseModel):
    """
    Loads a TOML file based on the module name and validates it 
    against a Pydantic schema.
    """
    file_path = CONFIG_DIR / f"{module_name}.toml"
    
    data = {}
    if file_path.exists():
        with open(file_path, "rb") as f:
            data = tomllib.load(f)
    else:
        # File doesn't exist? Create one using the Pydantic defaults!
        obj = schema() 
        with open(file_path, "w") as f:
            # .json() is a trick to get a dict in Pydantic v1
            import json
            defaults = json.loads(obj.json())
            f.write(f"# Auto-generated config for {module_name}\n")
            for section, values in defaults.items():
                f.write(f"\n[{section}]\n")
                for k, v in values.items():
                    f.write(f"{k} = {repr(v)}\n")
        return obj
            
    return schema(**data)