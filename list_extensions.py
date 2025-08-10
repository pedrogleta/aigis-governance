import vertexai
from vertexai.preview import extensions


vertexai.init(project="mars-prd", location="us-central1")

extensions_list = extensions.Extension.list()
print(extensions_list)

# for extension in extensions_list:
#     extension = extensions.Extension(extension.name)
#     extension.delete()
