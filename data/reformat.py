import json

input_file_path1 = 'ingredients.json'
input_file_path2 = 'tags.json'
output_file_path = 'foodgram_ingredients_tags_fixture.json'

app_name = 'recipes'
model_name_1 = 'Ingredient'
model_name_2 = 'Tag'

with (open(input_file_path1, 'r', encoding='utf-8') as input_file1,
      open(input_file_path2, 'r', encoding='utf-8') as input_file2):
    ingredients = json.load(input_file1)
    tags = json.load(input_file2)

formatted_data = []
for index, ingredient in enumerate(ingredients, start=1):
    formatted_data.append({
        "model": f"{app_name}.{model_name_1.lower()}",
        "pk": index,
        "fields": {
            "name": ingredient["name"],
            "measurement_unit": ingredient["measurement_unit"]
        }
    })
for index, tag in enumerate(tags, start=1):
    formatted_data.append({
        "model": f"{app_name}.{model_name_2.lower()}",
        "pk": index,
        "fields": {
            "name": tag["name"],
            "slug": tag["slug"]
        }
    })

with open(output_file_path, 'w', encoding='utf-8') as output_file:
    json.dump(formatted_data, output_file, ensure_ascii=False, indent=2)
