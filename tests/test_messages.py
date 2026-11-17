"""
Messages affichés par l'app : libellé de niveau correct et protection contre la
traduction automatique du navigateur (cause de « Risque ÉCHEC » à la place de
« Risque FAIBLE »).
"""
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.modules['streamlit'] = MagicMock()
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from streamlit_app.utils_simple import risk_message, NO_TRANSLATE_JS


@pytest.mark.parametrize('risque,kind,texte', [
    (0.1, 'success', "✅ Risque FAIBLE (< 1 %)"),
    (14.9, 'success', "✅ Risque FAIBLE (14.9%)"),
    (15.0, 'warning', "⚠️ Risque MOYEN (15.0%)"),
    (34.9, 'warning', "⚠️ Risque MOYEN (34.9%)"),
    (35.0, 'error', "🚨 Risque ÉLEVÉ (35.0%)"),
    (100.0, 'error', "🚨 Risque ÉLEVÉ (100.0%)"),
])
def test_message_sous_la_jauge(risque, kind, texte):
    assert risk_message(risque) == (kind, texte)


def test_aucun_echec_dans_les_messages_de_niveau():
    for risque in [0, 0.5, 5, 15, 25, 35, 60, 100]:
        assert 'CHEC' not in risk_message(risque)[1].upper()


def test_aucun_echec_dans_le_code_de_l_app():
    fichiers = list((ROOT / 'streamlit_app').glob('*.py')) + list((ROOT / 'src').glob('*.py'))
    for f in fichiers:
        code = [l for l in f.read_text(encoding='utf-8-sig').splitlines() if not l.strip().startswith('#')]
        for line in code:
            assert not re.search(r'[ÉE]CHEC', line), f"{f.name}: {line.strip()}"


def test_page_declaree_en_francais_et_non_traduisible():
    assert "lang = 'fr'" in NO_TRANSLATE_JS
    assert "'translate', 'no'" in NO_TRANSLATE_JS
    assert 'notranslate' in NO_TRANSLATE_JS
    app = (ROOT / 'streamlit_app' / 'app.py').read_text(encoding='utf-8-sig')
    assert 'components.html(NO_TRANSLATE_JS, height=0)' in app


def test_dockerfile_desactive_la_traduction():
    dockerfile = (ROOT / 'Dockerfile').read_text(encoding='utf-8')
    assert '<html lang="fr" translate="no">' in dockerfile
    assert 'content="notranslate"' in dockerfile
