def apply_projection(profile: dict, config: dict) -> dict:
    """Applies the runtime config to reshape the output profile."""
    if not config or "fields" not in config:
        return profile # Return original if no valid config is provided

    projected = {}
    on_missing = config.get("on_missing", "omit") # Default behavior is to omit

    for field_def in config["fields"]:
        target_path = field_def.get("path")
        # If 'from' isn't provided, assume the source key is the same as the target path
        source_path = field_def.get("from", target_path) 

        val = None
        # Handle basic array indexing (e.g., "emails[0]")
        if "[" in source_path and "]" in source_path:
            base_key, idx_str = source_path.replace("]", "").split("[")
            idx = int(idx_str)
            arr = profile.get(base_key, [])
            if arr and len(arr) > idx:
                val = arr[idx]
        else:
            # Handle standard flat keys
            val = profile.get(source_path)

        # Handle missing values based on config rules
        if val is None or val == "" or val == []:
            if on_missing == "null":
                projected[target_path] = None
            # If on_missing is "omit", we just do nothing and skip adding it
        else:
            projected[target_path] = val

    return projected