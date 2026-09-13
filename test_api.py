import urllib.request
import json
req = urllib.request.Request('http://localhost:8000/api/v1/projects', 
    data=json.dumps({'title': 'Emoji Strip Test', 'style': 'Explainer', 'language': 'en', 'script_content': 'Is the moon really made of cheese?'}).encode('utf-8'), 
    headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
proj = json.loads(res.read().decode('utf-8'))
print('PROJECT ID:', proj['id'])

req2 = urllib.request.Request('http://localhost:8000/api/v1/scenes/project/' + proj['id'])
res2 = urllib.request.urlopen(req2)
scenes = json.loads(res2.read().decode('utf-8'))
print('SCENE PROMPT:', scenes[0]['image_prompt'])
print('SCENE NARRATION:', scenes[0]['narration'])