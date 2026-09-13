import re
from typing import List, Dict, Any
from app.schemas.character import CharacterDNA


class CharacterDetectorService:
    """
    Automatically detects people, animals, robots, named entities,
    and professional roles in scripts to build reusable Character DNA objects.
    """

    ROLE_KEYWORDS = [
        'teacher', 'doctor', 'mother', 'father', 'police', 'officer', 'monk',
        'sadhu', 'king', 'queen', 'student', 'boy', 'girl', 'man', 'woman',
        'lion', 'tiger', 'robot', 'alien', 'warrior', 'guide', 'friend'
    ]

    @classmethod
    def detect_characters(cls, script_text: str) -> List[Dict[str, Any]]:
        if not script_text:
            return []

        text_lower = script_text.lower()
        found_characters: Dict[str, Dict[str, Any]] = {}

        # 1. Detect capitalized proper names only when they appear mid-sentence or are common names
        # Avoid treating sentence-initial words like "Top", "First", "Once" as character names
        COMMON_WORDS = {
            "the", "and", "for", "with", "this", "that", "when", "what", "here", "there",
            "top", "first", "second", "third", "one", "two", "three", "four", "five", "six",
            "many", "some", "every", "each", "all", "after", "before", "during", "while",
            "once", "then", "soon", "later", "finally", "overall", "however", "therefore",
            "how", "why", "who", "which", "where", "because", "since", "today", "yesterday",
            "tomorrow", "always", "never", "sometimes", "often", "almost", "about", "around",
            "facts", "fact", "secrets", "secret", "rules", "rule", "steps", "step", "tips",
            "life", "world", "earth", "space", "water", "fire", "light", "dark", "mind",
            "ancient", "modern", "future", "history", "science", "nature", "great", "best"
        }
        # Look for capitalized words that are NOT at the start of a sentence or line
        mid_sentence_names = re.findall(r'(?<=[a-z,;]\s)[A-Z][a-z]{2,15}\b', script_text)
        for name in mid_sentence_names:
            if name.lower() not in COMMON_WORDS and len(name) > 2:
                key = name.lower()
                if key not in found_characters:
                    dna = CharacterDNA(
                        age=24,
                        gender="Male" if name.endswith(('al', 'am', 'an', 'ar', 'ur', 'it')) else "Female",
                        hair_color="Black",
                        skin_tone="Medium",
                        outfit="Casual modern shirt and trousers",
                        accessories=["Wristwatch"]
                    )
                    found_characters[key] = {
                        "name": name,
                        "role": "Protagonist",
                        "dna": dna.model_dump()
                    }

        # 2. Detect professional roles or entities
        for role in cls.ROLE_KEYWORDS:
            if role in text_lower:
                if role not in found_characters:
                    role_title = role.capitalize()
                    gender = "Male" if role in ['boy', 'man', 'father', 'king', 'sadhu', 'monk'] else "Female" if role in ['girl', 'woman', 'mother', 'queen'] else "Neutral"
                    
                    outfit_map = {
                        'doctor': 'White lab coat and stethoscope',
                        'police': 'Official khaki police uniform',
                        'teacher': 'Formal shirt and trousers',
                        'sadhu': 'Traditional saffron spiritual robes',
                        'monk': 'Traditional maroon monk robes',
                        'robot': 'Futuristic metallic chrome armor',
                        'lion': 'Majestic golden fur'
                    }

                    dna = CharacterDNA(
                        age=35 if role in ['doctor', 'mother', 'father', 'police', 'teacher'] else 60 if role in ['sadhu', 'monk'] else 25,
                        gender=gender,
                        hair_color="Black" if role != 'robot' else "None",
                        skin_tone="Medium",
                        outfit=outfit_map.get(role, "Standard role outfit"),
                        accessories=["Role badge"] if role == 'police' else ["Stethoscope"] if role == 'doctor' else []
                    )

                    found_characters[role] = {
                        "name": f"The {role_title}",
                        "role": role_title,
                        "dna": dna.model_dump()
                    }

        # 3. Detect Hindi roles and cultural entities
        HINDI_ROLE_KEYWORDS = {
            'राजकुमार': {'name': 'The Prince', 'role': 'Prince', 'gender': 'Male', 'outfit': 'Regal royal Indian sherwani with gold embroidery and royal turban', 'age': 26},
            'राजा': {'name': 'The King', 'role': 'King', 'gender': 'Male', 'outfit': 'Royal crown and majestic ornate royal robes', 'age': 48},
            'रानी': {'name': 'The Queen', 'role': 'Queen', 'gender': 'Female', 'outfit': 'Royal silk saree with traditional jewelry', 'age': 45},
            'राजकुमारी': {'name': 'The Princess', 'role': 'Princess', 'gender': 'Female', 'outfit': 'Elegant silk royal lehenga with gold jewelry', 'age': 22},
            'साधु': {'name': 'The Sadhu', 'role': 'Spiritual Guide', 'gender': 'Male', 'outfit': 'Traditional saffron spiritual robes with rudraksha beads', 'age': 60},
            'किसान': {'name': 'The Farmer', 'role': 'Farmer', 'gender': 'Male', 'outfit': 'Simple rural cotton dhoti and kurta', 'age': 40},
            'मजदूर': {'name': 'The Laborer', 'role': 'Worker', 'gender': 'Male', 'outfit': 'Durable cotton work attire and headcloth', 'age': 32},
        }
        for kw, info in HINDI_ROLE_KEYWORDS.items():
            if kw in script_text:
                if info['role'].lower() not in found_characters:
                    dna = CharacterDNA(
                        age=info['age'],
                        gender=info['gender'],
                        hair_color="Black",
                        skin_tone="Medium",
                        outfit=info['outfit'],
                        accessories=["Royal brooch"] if "Prince" in info['role'] or "King" in info['role'] else []
                    )
                    found_characters[info['role'].lower()] = {
                        "name": info['name'],
                        "role": info['role'],
                        "dna": dna.model_dump()
                    }

        # Do NOT force a fake character if the script has no characters (e.g. nature, sci-fi, science)
        return list(found_characters.values())