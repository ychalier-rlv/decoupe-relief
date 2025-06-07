import math
import shutil
import subprocess
from pathlib import Path
import PIL.Image


# Chemin vers l'image de la carte de profondeur
depthmap_path = Path("depthmap.png")
# Dossier de sortie
output = Path("out")
# Chemin vers InkScape
inkscape_path = Path("C:\\Program Files\\Inkscape\\bin\\inkscape.exe")

# Nombre de feuillets
n = 128
# Nombre de lignes de feuillets par page
nrows = 9
# Nombre de colonnes de feuillets par page
ncols = 3
# Longeur d'un feuillet en millimètres
width = 60
# Largeur d'un feuillet en millimètres
height = 30
# Écart entre chaque feuillet en millimètres
padding = 1
# Profondeur maximale de la gravure en millimètres
depth_factor = 7
# Taille des trous en millimètres
hole = 1.5

# Nombre de points le long de la tranche gravée
res = 500
# Facteur de lissage
smooth_window = 10
# Facteur de mise à l'échelle du fichier PNG en sortie
scale = 20


img = PIL.Image.open(depthmap_path.as_posix()).resize((res, n))
if output.exists():
    shutil.rmtree(output)
output.mkdir()
nsheets = math.ceil(n / nrows / ncols)
for k in range(nsheets):
    svg = f"""<svg width="{scale * 210}" height="{scale * 297}" xmlns="http://www.w3.org/2000/svg">"""
    for i in range(nrows):
        for j in range(ncols):
            l = k * nrows * ncols + i * ncols + j
            if l >= n:
                break
            oy = i * (height + padding)
            ox = j * (width + padding)
            depths = [img.getpixel((x, l))[0] / 255 for x in range(res - 1, -1, -1)]
            for p in range(len(depths)):
                total = count = 0
                for q in range(-smooth_window, smooth_window+1):
                    if p + q >= 0 and p + q < len(depths):
                        total += depths[p + q]
                        count += 1
                depths[p] = total / count
            svg += """\t<path fill="black" fill-rule="evenodd" d=" """
            for x, depth in zip(range(res - 1, -1, -1), depths):
                px = ox + width - depth * depth_factor
                py = oy + height - x / (res - 1) * height
                if x == res - 1:
                    svg += f"M {scale * ox} {scale * oy} "
                svg += f"""L {scale * px:.0f} {scale * py:.0f} """
            svg += f"""L {scale * ox} {scale * (oy + height)} L {scale * ox} {scale * oy} Z """
            svg += f"""M {scale * (ox + 5)} {scale * (oy + 5)} l 0 {scale * hole} l {scale * hole} 0 l 0 {-scale * hole} l {-scale * hole} 0 Z """
            svg += f"""M {scale * (ox + 5)} {scale * (oy + height - 5 - hole)} l 0 {scale * hole} l {scale * hole} 0 l 0 {-scale * hole} l {-scale * hole} 0 Z """
            svg += """ "/>\n"""
    rect_size = 1 * scale
    svg += f"""<rect fill="black" width="{rect_size}" height="{rect_size}" x="{scale * 210 - rect_size}" y="{scale * 297 - rect_size}"/>"""
    svg += """</svg>"""
    path = output / f"{k}.svg" 
    with path.open("w") as file:
        file.write(svg)


for path in output.glob("*.svg"):
    subprocess.call([
        inkscape_path.absolute().as_posix(),
        """--actions="export-dpi:300;export-type:png;export-do;""",
        path.absolute().as_posix()
    ], cwd=inkscape_path.parent.absolute().as_posix(),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
