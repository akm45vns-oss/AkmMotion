import pytest
from app.services.ai.script_analyzer import ScriptAnalyzerService


@pytest.mark.asyncio
async def test_short_script_fast_path_hi_ayush():
    """
    TEST 1:
    Input: "HI AYUSH"
    Expected:
    - Exactly 1 scene
    - Scene narration: "HI AYUSH"
    - Subtitle: "HI AYUSH"
    - Zero additional words
    """
    analyzer = ScriptAnalyzerService()
    scenes = await analyzer.analyze_script("HI AYUSH", style="Explainer", language="en")

    assert len(scenes) == 1, f"Expected exactly 1 scene for 'HI AYUSH', got {len(scenes)}"
    scene = scenes[0]
    assert scene["narration"].strip() == "HI AYUSH"
    assert scene["subtitle"].strip() == "HI AYUSH"
    assert "image_prompt" in scene and len(scene["image_prompt"]) > 10


@pytest.mark.asyncio
async def test_short_script_two_sentences():
    """
    TEST 2:
    Input: "Hello everyone. Welcome to my channel."
    Expected:
    - 1 or 2 scenes depending on segmentation rules
    - ONLY the original text may appear across scenes
    - Zero added narration or dialogue
    """
    analyzer = ScriptAnalyzerService()
    script = "Hello everyone. Welcome to my channel."
    scenes = await analyzer.analyze_script(script, style="Vlog", language="en")

    assert 1 <= len(scenes) <= 2, f"Expected 1 or 2 scenes, got {len(scenes)}"
    concatenated = " ".join(s["narration"].strip() for s in scenes)
    
    # Check that only original words appear
    orig_words = set(script.lower().replace(".", "").split())
    scene_words = set(concatenated.lower().replace(".", "").split())
    assert scene_words.issubset(orig_words), f"Extra words found in narration: {scene_words - orig_words}"


@pytest.mark.asyncio
async def test_short_script_single_sentence():
    """
    TEST 3:
    Input: "This is a very short educational video."
    Expected:
    - Exactly 1 scene
    - Original text preserved verbatim
    """
    analyzer = ScriptAnalyzerService()
    script = "This is a very short educational video."
    scenes = await analyzer.analyze_script(script, style="Explainer", language="en")

    assert len(scenes) == 1, f"Expected 1 scene, got {len(scenes)}"
    assert scenes[0]["narration"].strip() == script


@pytest.mark.asyncio
async def test_longer_script_derives_only_from_original():
    """
    TEST 4:
    Input: ~100-word script
    Expected:
    - Reasonable scene count (2 to 4 scenes)
    - Every scene script must derive from the original script without added text
    """
    analyzer = ScriptAnalyzerService()
    sentences = [
        "Varanasi is one of the oldest living cities in the world.",
        "Pilgrims travel from all over to witness the evening Ganga Aarti.",
        "The priests perform rhythmic rituals with large brass lamps.",
        "Smoke from incense drifts into the night sky as chants echo along the ghats.",
        "The bells ring continuously while thousands of floating diyas illuminate the river.",
        "Every corner of this ancient city holds centuries of spiritual history and devotion.",
    ]
    script = " ".join(sentences)
    word_count = len(script.split())
    assert word_count >= 70

    scenes = await analyzer.analyze_script(script, style="Cinematic", language="en")

    # Reasonable scene count (2 to 4 scenes for ~80-100 words)
    assert 2 <= len(scenes) <= 4, f"Expected 2-4 scenes, got {len(scenes)}"

    # All generated narrations must only use words from original script
    orig_words = set(script.lower().replace(".", "").replace(",", "").split())
    concat_narration = " ".join(s["narration"] for s in scenes)
    concat_words = set(concat_narration.lower().replace(".", "").replace(",", "").split())

    extra_words = concat_words - orig_words
    assert len(extra_words) == 0, f"Found extra words in scenes: {extra_words}"


def test_validator_rejects_hallucinated_expansion():
    """
    TEST 5:
    Attempt an LLM response containing:
    "HI AYUSH. Today I will teach you five amazing tricks."
    The validator must reject the invented second sentence.
    """
    original_script = "HI AYUSH"
    hallucinated_scenes = [
        {
            "scene_number": 1,
            "narration": "HI AYUSH. Today I will teach you five amazing tricks.",
            "subtitle": "HI AYUSH. Today I will teach you five amazing tricks.",
            "image_prompt": "Cinematic shot of Ayush waving.",
        }
    ]

    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(
        original_script, hallucinated_scenes, max_scenes=1
    )

    assert is_valid is False, "Validator should have rejected hallucinated second sentence"
    assert "extra words" in reason.lower() or "inserted" in reason.lower()


def test_validator_rejects_exceeded_scene_count():
    """
    Validator rejects responses exceeding max_scenes.
    """
    original_script = "HI AYUSH"
    eight_scenes = [
        {
            "scene_number": i,
            "narration": "HI AYUSH",
            "subtitle": "HI AYUSH",
            "image_prompt": f"Scene {i}",
        }
        for i in range(1, 9)
    ]

    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(
        original_script, eight_scenes, max_scenes=1
    )

    assert is_valid is False
    assert "exceeds maximum allowed" in reason


def test_calculate_scene_count_policy():
    """
    TEST 6:
    Verifies scene count policy bounds:
    - 0-20 words (1 sentence) -> (1, 1)
    - 21-50 words -> max 2
    - 51-100 words -> max 3
    - 101-180 words -> max 4
    - 181-300 words -> max 6
    """
    # 2 words, 1 sentence
    t, m = ScriptAnalyzerService.calculate_scene_count("HI AYUSH")
    assert t == 1 and m == 1

    # 15 words, 1 sentence
    t, m = ScriptAnalyzerService.calculate_scene_count(
        "This is a single sentence containing approximately fifteen words describing an educational concept clearly."
    )
    assert t == 1 and m == 1

    # 40 words
    t, m = ScriptAnalyzerService.calculate_scene_count("word " * 40)
    assert m <= 2

    # 80 words
    t, m = ScriptAnalyzerService.calculate_scene_count("word " * 80)
    assert m <= 3

    # 150 words
    t, m = ScriptAnalyzerService.calculate_scene_count("word " * 150)
    assert m <= 4


# ─────────────────────────────────────────────────────────────────────────────
# HARDENING REGRESSION TESTS: Exact Invariant & Token Fidelity
# ─────────────────────────────────────────────────────────────────────────────

def test_validator_rejects_duplicated_words():
    """
    Duplicated words that were not in the original script must be rejected.
    """
    original = "Focus on your breathing and relax completely."
    scenes = [
        {
            "scene_number": 1,
            "narration": "Focus focus on your breathing and relax completely.",
            "subtitle": "Focus focus on your breathing and relax completely.",
            "image_prompt": "Calm meditation space",
        }
    ]
    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(original, scenes, max_scenes=1)
    assert is_valid is False
    assert "extra words" in reason.lower() or "inserted" in reason.lower()


def test_validator_rejects_reordered_words():
    """
    Words must maintain exact sequence order. Swapping adjacent words must fail.
    """
    original = "Start your morning with cold water."
    scenes = [
        {
            "scene_number": 1,
            "narration": "Start morning your with cold water.",
            "subtitle": "Start morning your with cold water.",
            "image_prompt": "Morning kitchen glass of water",
        }
    ]
    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(original, scenes, max_scenes=1)
    assert is_valid is False
    assert "mismatch" in reason.lower() or "reordering" in reason.lower()


def test_validator_rejects_omitted_words():
    """
    Dropping any word from the user's script must fail validation.
    """
    original = "Exercise daily to maintain physical and mental strength."
    scenes = [
        {
            "scene_number": 1,
            "narration": "Exercise daily to maintain physical strength.",
            "subtitle": "Exercise daily to maintain physical strength.",
            "image_prompt": "Athlete training",
        }
    ]
    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(original, scenes, max_scenes=1)
    assert is_valid is False
    assert "omitted" in reason.lower() or "missing" in reason.lower()


def test_validator_rejects_inserted_words():
    """
    Inserting commentary, adjectives, or conversational fillers must fail validation.
    """
    original = "Consistency is the path to mastery."
    scenes = [
        {
            "scene_number": 1,
            "narration": "Consistency is really the true path to mastery.",
            "subtitle": "Consistency is really the true path to mastery.",
            "image_prompt": "Monk practicing calligraphy",
        }
    ]
    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(original, scenes, max_scenes=1)
    assert is_valid is False
    assert "extra words" in reason.lower() or "inserted" in reason.lower()


def test_validator_accepts_exact_multi_scene_reconstruction():
    """
    Concatenating all scene narrations in order must reconstruct 100% of original tokens.
    """
    original = "The sun rises over the Himalayas. Monks begin their morning chants in silence. The bells echo across the valley."
    scenes = [
        {
            "scene_number": 1,
            "narration": "The sun rises over the Himalayas.",
            "subtitle": "The sun rises over the Himalayas.",
            "image_prompt": "Sunrise over snowcapped mountain peaks",
        },
        {
            "scene_number": 2,
            "narration": "Monks begin their morning chants in silence.",
            "subtitle": "Monks begin their morning chants in silence.",
            "image_prompt": "Monks meditating in monastery hall",
        },
        {
            "scene_number": 3,
            "narration": "The bells echo across the valley.",
            "subtitle": "The bells echo across the valley.",
            "image_prompt": "Ancient brass temple bell swinging",
        },
    ]
    is_valid, reason = ScriptAnalyzerService.validate_script_fidelity(original, scenes, max_scenes=3)
    assert is_valid is True, f"Validation failed: {reason}"
    assert reason == "Valid"


def test_harmonized_duration_pacing():
    """
    Verify calculate_estimated_duration returns consistent, bounded values:
    - 2 words -> 3.0s minimum
    - 10 words -> ~4.5s
    - 50 words / 2 scenes -> 20.0s (10.0s max per scene)
    """
    assert ScriptAnalyzerService.calculate_estimated_duration(0) == 0.0
    assert ScriptAnalyzerService.calculate_estimated_duration(2, 1) == 3.0
    assert ScriptAnalyzerService.calculate_estimated_duration(10, 1) == 4.5
    assert ScriptAnalyzerService.calculate_estimated_duration(50, 2) == 20.0
