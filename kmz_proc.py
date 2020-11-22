import glob, csv, os
import pandas as pd
from lxml import html
from zipfile import ZipFile
from PIL import Image

pd.options.mode.chained_assignment = None

ZIP_KML_DOC = "doc.kml"
CSV_KML_DOC = "kml_index.csv"
ZIP_KMZ_IMG_FOLDER = "files"
KMZ_GLOBAL_IMAGE = "map.jpg"

class KMZ:
    def __init__(self) -> None:
        self.kmz_zip = ZipFile(glob.glob("*.kmz")[0], "r")
        if not os.path.isfile(CSV_KML_DOC):
            self.kml_file = self.kmz_zip.open(ZIP_KML_DOC, "r").read()
            self._indexer_csv()
        self._load_df()
        self._arrange_df()

    def _indexer_csv(self,) -> None:
        kml_content = html.fromstring(self.kml_file)
        with open(CSV_KML_DOC, "w", newline="") as kml_csv:
            kml_csv_writer = csv.writer(kml_csv)
            kml_csv_writer.writerow(
                ["index", "image", "draw_order", "north", "south", "east", "west", "rotation"]
            )
            for item in kml_content.cssselect("Document GroundOverlay"):
                image = item.cssselect("name")[0].text_content()
                index = image[23:-4]
                draw_order = item.cssselect("drawOrder")[0].text_content()
                coords = item.cssselect("LatLonBox")[0]
                north = coords.cssselect("north")[0].text_content()
                south = coords.cssselect("south")[0].text_content()
                east = coords.cssselect("east")[0].text_content()
                west = coords.cssselect("west")[0].text_content()
                rotation = coords.cssselect("rotation")[0].text_content()
                kml_csv_writer.writerow(
                    [index, image, draw_order, north, south, east, west, rotation]
                )

    def _load_df(self, ) -> None:
        self.df = pd.read_csv(CSV_KML_DOC)
        self.df.sort_values(by='north', ascending=False, inplace = True)

    def _arrange_df(self, ) -> None:
        self.globe_matrix = []
        for i, row in self.df.iterrows():
            sub_df = self.df.loc[(self.df['north'] == row['north']) & (self.df['south'] == row['south'])]
            if sub_df.empty:
                continue
            else:
                sub_df.sort_values(by='west', inplace = True)
                self.globe_matrix.append(sub_df)
                self.df.drop(sub_df.index, inplace = True)

    def _find_coords_item(self, coords: list) -> list:
        if myloc[0] > 0: # first 10
            gset = [None, -7]
            if myloc[1] > 0: # last 21
                sset = [22, None]
            else:
                sset = [None, -21]
        else: # last 7
            gset = [10, None]
            if myloc[1] > 0: # last 21
                sset = [22, None]
            else:
                sset = [None, -21]

        for item in self.globe_matrix[gset[0]:gset[1]]:
            for i, row in item.iloc[sset[0]:sset[1]].iterrows():
                if (row['north'] >= myloc[0] >= row['south']) and (row['west'] <= myloc[1] <= row['east']):
                    return row.tolist()

    def _load_images(self, images) -> list:
        if images:
            self.kmz_imgs = [Image.open(self.kmz_zip.open(ZIP_KMZ_IMG_FOLDER+"/"+image)) for image in images]
        else:
            self.kmz_imgs = [Image.open(self.kmz_zip.open(image)) for image in self.kmz_zip.namelist() if image.split("/")[0] == ZIP_KMZ_IMG_FOLDER]
        return self.kmz_imgs

    def _generate_image(self, images: list, fullvh=False, vertical=False, horizontal=False):
        if horizontal:
            widths, heights = zip(*(img.size for img in images))
            total_width = sum(widths)
            max_height = max(heights)

            new_image = Image.new('RGB', (total_width, max_height))
            x_offset = 0
            for img in images:
                new_image.paste(img, (x_offset,0))
                x_offset += img.size[0]

        elif vertical:
            widths, heights = zip(*(img.size for img in images))
            max_width = max(widths)
            total_height = sum(heights)

            new_image = Image.new('RGB', (max_width, total_height))
            y_offset = 0
            for img in images:
                new_image.paste(img, (0,y_offset))
                y_offset += img.size[1]
        elif fullvh:
            vertical_set = [self._generate_image(image, horizontal=True) for image in images]
            new_image = self._generate_image(vertical_set, vertical=True)

        return new_image

    def global_imager(self, ) -> None:
        globe_images = [self._load_images(matrix["image"].tolist()) for matrix in self.globe_matrix]
        self._generate_image(globe_images, fullvh=True).save(KMZ_GLOBAL_IMAGE)


if __name__ == "__main__":
    myloc = [52.379971, 4.8196657]

    kmz = KMZ()
    #kmz.global_imager()

    print(kmz._find_coords_item(myloc))
