def validate_request(data):
    errors = []
    required = ['query', 'breadth', 'depth', 'mode']
    
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if 'mode' in data and data['mode'] not in ['report', 'answer']:
        errors.append("Mode must be 'report' or 'answer'")
    
    if 'breadth' in data and not 2 <= data['breadth'] <= 10:
        errors.append("Breadth must be between 2-10")
    
    if 'depth' in data and not 1 <= data['depth'] <= 5:
        errors.append("Depth must be between 1-5")
    
    return errors