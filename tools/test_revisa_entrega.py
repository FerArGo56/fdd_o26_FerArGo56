"""Guardas de la revision automatica de entregas.

El script vive en .github/scripts/ y decide si un pull request de estudiante se
acepta. Un falso positivo aqui bloquea a alguien que hizo todo bien, asi que
las reglas se prueban en las dos direcciones.

Varias de estas pruebas existen por un hallazgo concreto de una revision
adversarial; cada una dice cual.
"""
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / ".github/scripts/revisa_entrega.py"
WORKFLOW = RAIZ / ".github/workflows/entregas.yml"


def _cargar():
    assert SCRIPT.is_file(), "falta .github/scripts/revisa_entrega.py"
    spec = importlib.util.spec_from_file_location("revisa_entrega", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def mod():
    return _cargar()


@pytest.fixture
def wf():
    """El workflow parseado. `on:` se carga como el booleano True en YAML 1.1."""
    d = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return d


def _f(path, status="added", previa=""):
    return {"path": path, "status": status, "previa": previa}


def _correr(mod, monkeypatch, archivos, autor="ana", rama="tarea-07-git",
            mantenedores="uumami", rama_default="main", declarado=None,
            estricta_desde=""):
    monkeypatch.setenv("AUTOR", autor)
    monkeypatch.setenv("RAMA", rama)
    monkeypatch.setenv("RAMA_DEFAULT", rama_default)
    monkeypatch.setenv("PR", "1")
    monkeypatch.setenv("MANTENEDORES", mantenedores)
    monkeypatch.setenv("BRANCH_ESTRICTA_DESDE", estricta_desde)
    monkeypatch.setenv("GITHUB_REPOSITORY", "raya-lucaria/fdd_o26")
    monkeypatch.setattr(mod, "archivos_del_pr", lambda pr: archivos)
    n = len(archivos) if declarado is None else declarado
    monkeypatch.setattr(mod, "total_declarado", lambda pr: n)
    return mod.main()


# --- las cuatro reglas, en las dos direcciones -------------------------------

def test_entrega_correcta_pasa(mod, monkeypatch):
    archivos = [_f("estudiantes/ana/07_git/bitacora.md"),
                _f("estudiantes/ana/07_git/ejemplo.sh")]
    assert _correr(mod, monkeypatch, archivos) == 0


def test_tocar_la_zona_roja_falla(mod, monkeypatch):
    archivos = [_f("estudiantes/ana/07_git/bitacora.md"),
                _f("codigo/07_git/ejemplo.sh", "modified")]
    assert _correr(mod, monkeypatch, archivos) == 1


def test_tocar_la_carpeta_de_otro_falla(mod, monkeypatch):
    assert _correr(mod, monkeypatch, [_f("estudiantes/beto/07_git/a.md")]) == 1


def test_carpeta_con_mayusculas_distintas_falla(mod, monkeypatch):
    """Los logins de GitHub no distinguen mayusculas; las rutas si."""
    assert _correr(mod, monkeypatch, [_f("estudiantes/Ana/07_git/a.md")]) == 1


def test_basura_agregada_falla(mod, monkeypatch):
    for ruta in ("estudiantes/ana/07_git/.DS_Store",
                 "estudiantes/ana/07_git/__pycache__/x.pyc",
                 "estudiantes/ana/.env"):
        assert _correr(mod, monkeypatch, [_f(ruta)]) == 1, ruta


def test_borrar_basura_no_falla(mod, monkeypatch):
    """El falso positivo clasico: borrar un .DS_Store es la accion correcta."""
    archivos = [_f("estudiantes/ana/07_git/.DS_Store", "removed"),
                _f("estudiantes/ana/07_git/bitacora.md", "modified")]
    assert _correr(mod, monkeypatch, archivos) == 0


def test_pull_request_desde_main_falla(mod, monkeypatch):
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos, rama="main") == 1


def test_la_regla_de_branch_avisa_antes_de_la_fecha_de_corte(mod, monkeypatch, capsys):
    """El grupo ya tenia pull requests abiertos desde main cuando la regla
    entro, asi que hay un periodo de gracia con fecha explicita."""
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos, rama="main",
                   estricta_desde="2099-01-01") == 0
    salida = capsys.readouterr().out
    assert "AVISO" in salida and "2099-01-01" in salida


def test_la_regla_de_branch_rechaza_pasada_la_fecha(mod, monkeypatch):
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos, rama="main",
                   estricta_desde="2000-01-01") == 1


def test_sin_fecha_la_regla_es_estricta(mod, monkeypatch):
    """Borrar la variable del workflow endurece la regla, no la apaga."""
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos, rama="main",
                   estricta_desde="") == 1


def test_el_aviso_no_tapa_los_otros_fallos(mod, monkeypatch):
    """Estar en periodo de gracia no debe aprobar una entrega mal ubicada."""
    archivos = [_f("codigo/07_git/ejemplo.sh", "modified")]
    assert _correr(mod, monkeypatch, archivos, rama="main",
                   estricta_desde="2099-01-01") == 1


def test_el_workflow_declara_la_fecha_de_corte(wf):
    env = wf["jobs"]["revision"]["steps"][-1]["env"]
    assert "BRANCH_ESTRICTA_DESDE" in env, (
        "sin la fecha la regla es estricta; si eso es lo que se quiere, "
        "borra tambien esta prueba"
    )


def test_el_mantenedor_queda_exento(mod, monkeypatch):
    archivos = [_f("course/7_git_y_github/2_github/1_github_en_corto.md", "modified"),
                _f("codigo/07_git/ejemplo.sh", "modified")]
    assert _correr(mod, monkeypatch, archivos, autor="uumami", rama="main") == 0


def test_un_archivo_llamado_env_no_es_dotenv(mod, monkeypatch):
    """`.env` es basura; `env.md` o `mi.env.example` no lo son."""
    for ok in ("estudiantes/ana/07_git/env.md",
               "estudiantes/ana/07_git/mi.env.example",
               "estudiantes/ana/07_git/notas__pycache__.txt",
               "estudiantes/ana/07_git/como-borrar-DS_Store.md"):
        assert _correr(mod, monkeypatch, [_f(ok)]) == 0, ok


# --- hallazgos de la revision adversarial ------------------------------------

def test_rename_que_saca_un_archivo_de_la_zona_roja_falla(mod, monkeypatch):
    """La API sólo pone la ruta destino en `filename`. Sin `previous_filename`,
    un git mv de course/ a la propia carpeta pasaba en verde y el merge
    borraba el archivo del curso."""
    archivos = [_f("estudiantes/ana/07_git/robado.md", "renamed",
                   previa="course/2_pipeline_de_datos/4_cuando_se_rompe.md")]
    assert _correr(mod, monkeypatch, archivos) == 1


def test_rename_dentro_de_la_propia_carpeta_pasa(mod, monkeypatch):
    archivos = [_f("estudiantes/ana/07_git/nuevo.md", "renamed",
                   previa="estudiantes/ana/07_git/viejo.md")]
    assert _correr(mod, monkeypatch, archivos) == 0


def test_la_rama_default_no_es_siempre_main(mod, monkeypatch):
    """Un fork con rama default `master` entregaba desde su default sin que
    nadie se enterara."""
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos,
                   rama="master", rama_default="master") == 1
    # y una branch de tarea sigue pasando aunque la default sea master
    assert _correr(mod, monkeypatch, archivos,
                   rama="tarea-07-git", rama_default="master") == 0


def test_variantes_de_env_son_basura(mod, monkeypatch):
    """En un repositorio publico, .env.local con una llave es el caso grave."""
    for ruta in ("estudiantes/ana/.env.local", "estudiantes/ana/.env.production",
                 "estudiantes/ana/.envrc", "estudiantes/ana/id_rsa",
                 "estudiantes/ana/llave.pem"):
        assert _correr(mod, monkeypatch, [_f(ruta)]) == 1, ruta


def test_pull_request_vacio_no_es_una_entrega(mod, monkeypatch):
    assert _correr(mod, monkeypatch, []) == 1


def test_api_truncada_falla_cerrado(mod, monkeypatch):
    """La API corta en 3000 archivos. Si lo bajado no coincide con lo declarado,
    no podemos afirmar que revisamos la entrega completa."""
    archivos = [_f("estudiantes/ana/07_git/bitacora.md")]
    assert _correr(mod, monkeypatch, archivos, declarado=3001) == 1


def test_archivo_llamado_estudiantes_ana_va_a_ubicacion(mod, monkeypatch):
    """Antes producia el mensaje absurdo 'Esperaba estudiantes/ana/, encontre
    estudiantes/ana/'."""
    assert _correr(mod, monkeypatch, [_f("estudiantes/ana")]) == 1


def test_el_truncado_dice_cuantos_faltan(mod, monkeypatch, capsys):
    archivos = [_f(f"codigo/f{i}.md", "modified") for i in range(50)]
    assert _correr(mod, monkeypatch, archivos) == 1
    assert "y 30 mas." in capsys.readouterr().out


def test_prefijo_de_login_no_pasa(mod, monkeypatch):
    assert _correr(mod, monkeypatch, [_f("estudiantes/ana2/x.md")]) == 1
    assert _correr(mod, monkeypatch, [_f("estudiantes/ana/x.md")],
                   autor="ana2") == 1


# --- el workflow -------------------------------------------------------------

def test_el_workflow_usa_pull_request_target(wf):
    """Con `pull_request` el propio pull request reescribe este workflow y el
    script que lo juzga, y se aprueba solo."""
    disparador = wf.get("on", wf.get(True))
    assert list(disparador) == ["pull_request_target"], (
        "el disparador tiene que ser pull_request_target; con pull_request "
        "GitHub corre los archivos del fork"
    )


def test_el_checkout_va_fijado_a_la_base(wf):
    """`pull_request_target` sin esto trae el arbol del fork de todos modos."""
    pasos = wf["jobs"]["revision"]["steps"]
    checkout = [p for p in pasos if str(p.get("uses", "")).startswith("actions/checkout")]
    assert len(checkout) == 1, "se espera exactamente un checkout"
    assert checkout[0]["with"]["ref"] == "${{ github.event.pull_request.base.sha }}"
    assert checkout[0]["with"]["persist-credentials"] is False


def test_el_workflow_no_ejecuta_nada_del_pull_request(wf):
    """La regla que hace seguro a pull_request_target."""
    for paso in wf["jobs"]["revision"]["steps"]:
        run = paso.get("run", "")
        assert "head" not in run, f"un run no debe tocar el head del PR: {run}"


def test_permisos_de_solo_lectura(wf):
    assert wf["permissions"] == {"contents": "read", "pull-requests": "read"}


def test_el_workflow_exporta_lo_que_el_script_lee(wf, mod):
    env = wf["jobs"]["revision"]["steps"][-1]["env"]
    for clave in ("GH_TOKEN", "PR", "AUTOR", "RAMA", "RAMA_DEFAULT", "MANTENEDORES"):
        assert clave in env, f"el workflow no exporta {clave}"


def test_los_bots_quedan_exentos(wf):
    assert "'Bot'" in wf["jobs"]["revision"]["if"]
