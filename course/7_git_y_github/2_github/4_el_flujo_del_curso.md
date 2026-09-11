---
id: el-flujo-del-curso
title: "La zona roja y tu espejo"
nav_title: "Tu espejo"
summary: "Dónde puedes escribir y dónde no, por qué la regla existe, y cómo se copia el código de la clase a tu carpeta sin arruinar la entrega con un detalle de cp."
status: ready
estimated_time: 20m
tags: [flujo, mirror, estudiantes, conflicto, github-actions, disciplina]
prerequisites: [branches-en-serio]
---

# La zona roja y tu espejo

**GitHub · página 4 de 6** · 20 min

Meta: que nunca tengas que preguntar dónde va un archivo ni cómo se llama tu carpeta.

## En corto

- Zona **roja**: sólo se lee. Zona **verde**: tu carpeta, y sólo tu carpeta.
- Tu carpeta se llama exactamente como tu login, y es un **espejo** de `codigo/`: misma ruta, mismo nombre.
- La razón no es jerárquica: con una carpeta por persona, treinta pull requests se mergean sin conflictos.
- Una revisión automática lo comprueba antes de que yo lo vea.

## El mapa

```text
fdd_o26/
├── course/         ← ROJA   el sitio que estás leyendo
├── codigo/         ← ROJA   el código de cada unidad
│   ├── 07_git/
│   │   ├── bitacora.md
│   │   └── ejemplo.sh
│   └── github/     ← el de las tareas de DataCamp
├── tools/ skins/   ← ROJA   la maquinaria del sitio
├── raya.yaml       ← ROJA
└── estudiantes/
    ├── tu-login/   ← VERDE  TUYA. Escribes aquí, y sólo aquí
    │   └── 07_git/
    │       ├── bitacora.md   ← copia de codigo/07_git/
    │       └── ejemplo.sh    ← copia de codigo/07_git/
    └── otro-login/ ← de alguien más. No la toques
```

::: figure {#git-el-mirror title="Tu carpeta es un espejo"}
![Dos árboles de archivos lado a lado: a la izquierda en rojo la carpeta de código del curso que es de sólo lectura, y a la derecha en verde tu carpeta dentro de estudiantes con tu nombre de usuario de GitHub, con los mismos nombres de subcarpeta y archivo en los dos lados](../_assets/git-el-mirror.svg)
:::

## La regla del espejo

Se repite igual en todas las unidades del resto del curso. En inglés se le dice *mirror*, y así aparece en los mensajes:

> **Tu carpeta es un espejo de `codigo/`. Misma ruta, mismo nombre, sin excepciones.**
> Yo publico en `codigo/07_git/` y tú copias a `estudiantes/tu-login/07_git/`.

No se inventa el nombre. No se traduce al español. No se decide. No se pregunta.

## Cómo se copia

El espejo se copia **desde tu branch de tarea**, nunca desde `main`. Si vienes de la página anterior estás parado en `main`, así que lo primero es crearla:

```bash
cd ~/fdd/fdd_o26
git switch main
git switch -c tarea-07-git   # la branch de esta tarea
mkdir -p estudiantes/$GHUSER/07_git

# el espejo. Ojo con el "/." y con la barra final
cp -r codigo/07_git/. estudiantes/$GHUSER/07_git/

ls -R estudiantes/$GHUSER/07_git   # míralo completo
git restore codigo/           # si tocaste la zona roja
```

La **barra y el punto** al final del origen no son adorno:

```text
cp -r codigo/07_git/. estudiantes/$GHUSER/07_git/
 │  │            │  │                  └── con barra:
 │  │            │  │                     "dentro de esto"
 │  │            │  └── el punto: "el CONTENIDO de la carpeta"
 │  │            └───── la carpeta origen
 │  └────────────────── -r: recursivo, entra a las subcarpetas
 └───────────────────── copiar
```

::: table {#git-cp-punto title="La diferencia que arruina la entrega"}

| Comando | Si el destino no existe | Si el destino ya existe |
|---|---|---|
| `cp -r codigo/07_git dest/07_git` | Correcto | **Crea `07_git/07_git/`** |
| `cp -r codigo/07_git/. dest/07_git/` | Correcto | Correcto |

:::

Sin la barra y el punto, `cp` copia **la carpeta**; con ellos copia **su contenido**. La segunda vez que lo corras —porque publiqué un archivo nuevo— la primera forma te anida la carpeta dentro de sí misma.

> [!WARNING]
> No copies arrastrando en el Finder ni en el Explorador: producen `07_git copia` y `07_git - copia`, que no son el nombre del espejo. Usa la terminal.

## Por qué, y no es porque yo lo diga

::: figure {#git-race title="Dos personas, un repositorio"}
![Tres columnas con tres escenarios: en el primero cada persona toca un archivo distinto y funciona, en el segundo tocan el mismo archivo en líneas separadas y también funciona, y en el tercero tocan la misma línea y hay conflicto](../_assets/git-race.svg)
:::

En la página 3 te provocaste un conflicto. La condición que lo produjo fue muy específica: **dos versiones de la misma línea, del mismo archivo**. Ahora compara las dos formas de resolver el ejercicio de esta unidad:

```text
  EDITANDO codigo/ DIRECTO                          ✗
    Lun   yo publico  codigo/07_git/ejemplo.sh
    Mar   tú editas   codigo/07_git/ejemplo.sh
    Mié   yo corrijo  codigo/07_git/ejemplo.sh
    Jue   git merge upstream/main  →  CONFLICT
          ...y lo mismo a las otras 29 personas

  CON EL ESPEJO                                     ✓
    Lun   yo publico  codigo/07_git/ejemplo.sh
    Mar   tú copias → estudiantes/tu-login/07_git/
          y editas TU copia
    Mié   yo corrijo  codigo/07_git/ejemplo.sh
    Jue   git merge upstream/main  →  Fast-forward
          tu copia, intacta
```

![Ciudad densa bajo lluvia intensa en teal frío y concreto húmedo, vista desde lo alto entre dos torres enfrentadas: tras una ventana iluminada de cada torre trabaja una figura pequeña de espaldas, y un solo cable tenso une las dos ventanas con una gota de luz ámbar suspendida en el centro exacto, sin avanzar hacia ningún lado.](../_assets/ilus-git-colaboracion.jpg)

Nadie toca las líneas de nadie. Todos los casos se vuelven el primer escenario del diagrama. **Ésa es toda la razón de la regla.**

::: table {#git-zonas title="Qué puedes tocar"}

| Carpeta | Puedes escribir |
|---|---|
| `course/`, `codigo/`, `tools/`, `skins/`, `raya.yaml` | No |
| `estudiantes/otro-login/` | No |
| `estudiantes/tu-login/` | **Sí, y sólo ahí** |

:::

## Qué revisa la revisión automática

Cada pull request dispara una revisión antes de que yo lo vea. Está para que un error se detecte en treinta segundos y no en una semana. La única excepción es tu **primer** pull request del semestre: ése lo tengo que autorizar yo antes de que corra.

::: table {#git-robot title="Las cuatro revisiones, todas bloqueantes"}

| Revisa | Rechaza si |
|---|---|
| **Ubicación** | Tocaste algo fuera de `estudiantes/tu-login/` |
| **Nombre** | Tu carpeta no se llama exactamente como tu login |
| **Basura** | Agregaste `.DS_Store`, `Thumbs.db`, `__pycache__/`, `node_modules/`, `.venv/`, `*.pyc`, o algo que empiece con `.env` |
| **Branch** | El pull request viene de la branch default de tu fork |

:::

El mensaje siempre dice **qué archivo y qué hacer**. Borrar basura no cuenta como agregarla: la revisión ignora los borrados a propósito.

> [!NOTE]
> **Un pull request rechazado se corrige haciendo `push` a la misma branch.** No abras otro. El pull request se actualiza solo y la revisión se vuelve a correr.

![Un corredor técnico largo y estrecho partido en dos mitades por un umbral iluminado en ámbar: la mitad cercana es cálida y ordenada, con estantes alineados, y la lejana se disuelve en azul frío; en primer plano, de espaldas y en silueta, una figura se detiene un paso antes del umbral, sin cruzarlo.](../_assets/ilus-git-disciplina.jpg)

Se pide con una precisión que puede parecer excesiva. Hay dos razones:

- **El flujo es la parte que se automatiza.** No reviso a mano dónde pusiste cada archivo: lo revisa un programa, y un programa no interpreta intenciones. Una carpeta con nombre parecido es una carpeta equivocada.
- **Es cómo se trabaja después.** En cualquier equipo, un pull request que no pasa las revisiones no se mergea, por bueno que sea el código. Aprender el hábito aquí, donde equivocarse cuesta volver a intentar, es barato.

::: problem {#git-p11-colision title="Arreglé la errata en el archivo del profesor"}
Un compañero encuentra un error en `codigo/07_git/ejemplo.sh`. Lo arregla ahí mismo, hace commit en su branch de tarea, y abre el pull request pensando que hizo un favor.

La revisión se lo rechaza. Él argumenta, con razón, que su corrección es correcta.

¿Por qué se rechaza de todas formas, y cuál era la forma correcta de reportarlo?
:::

::: hint {of="git-p11-colision"}
La revisión no juzga si el contenido es bueno. Juzga dónde está. Y piensa qué pasa si los treinta hacen "un favor" el mismo martes.
:::

::: answer {of="git-p11-colision"}
Se rechaza porque tocó un archivo fuera de `estudiantes/su-login/`, y esa regla no admite excepciones por mérito. Si las admitiera dejaría de ser una regla que una máquina puede aplicar, y volveríamos a revisar treinta pull requests a mano para decidir cuáles merecen tocar la zona roja.

El costo tampoco es sólo mío. En el momento en que su commit toca `codigo/07_git/ejemplo.sh`, cualquier corrección que yo publique después choca con la suya, y el conflicto le aparece **a él** la próxima vez que se ponga al día. La regla lo protege a él tanto como a mí.

Lo correcto era mantener su copia arreglada en su carpeta —que es lo que iba a hacer de todas formas— y reportar la errata fuera del flujo de entrega: un issue, o decirlo en clase.

Vale la pena notar que **su instinto era bueno**. Lo que estaba mal era el canal, no la intención.
:::

> [!NOTE]
> **Si sólo recuerdas una cosa:** misma ruta, mismo nombre. Si en `codigo/` se llama `07_git`, en tu carpeta se llama `07_git`.

## Cierre

Ya sabes las reglas y por qué existen. En [[el-ritual-del-curso|El ritual]] están los comandos exactos, en orden, para ejecutarlas.
