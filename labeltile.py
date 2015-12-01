#!/usr/bin/env python3
import argparse
from collections import Counter
from math import ceil, floor
import colorsys
import logging
from PIL import Image, ImageDraw

__author__ = 'Morten Brekkevold <morten@snabel.org>'
__copyright__ = '(C) 2015 Morten Brekkevold'
__license__ = 'MIT'

_logger = logging.getLogger('beerlabeltile')

INCH = 25.4  # mm
A4 = (210, 297)  # mm
DEFAULT_DPI = 300
DEFAULT_COLOR = (0xff, 0xff, 0xff, 0x00)  # transparent white
LIGHTNESS_FACTOR = 1.1  # how much to raise the lightness for the grid color
GUIDE_WIDTH = 3  # pixels

def main():
    args = parse_args()
    logging.basicConfig(level=logging.getLevelName(args.loglevel.upper()))

    label = Image.open(args.inputfile)
    dpi_x, dpi_y = label.info.get('dpi', (DEFAULT_DPI, DEFAULT_DPI))
    ppmm = (dpi_x/INCH, dpi_y/INCH)
    _logger.debug("Image size: %sx%s (%3.1fx%3.1f mm)",
                  label.size[0], label.size[1],
                  label.size[0]/ppmm[0], label.size[1]/ppmm[1])

    sheet_size = (round(A4[0]*ppmm[0]), round(A4[1]*ppmm[1]))
    _logger.debug("Sheet size in pixels: %s", sheet_size)
    sheet = Image.new(mode="RGBA", size=sheet_size, color=DEFAULT_COLOR)

    fit_x = floor(sheet.size[0] / label.size[0])
    fit_y = floor(sheet.size[1] / label.size[1])

    _logger.debug("Can fit at most (%sx%s) = %s labels on one A4 sheet",
                  fit_x, fit_y, fit_x*fit_y)

    # Calculate placement of labels on sheet
    sum_width = fit_x * label.size[0] + GUIDE_WIDTH * (fit_x+1)
    sum_height = fit_y * label.size[1] + GUIDE_WIDTH * (fit_y+1)
    start_x = floor(sheet.size[0] / 2 - sum_width / 2)
    start_y = floor(sheet.size[1] / 2 - sum_height / 2)

    # Draw grid guides
    draw = ImageDraw.Draw(sheet)
    grid_color = calculate_grid_color(label)
    for y in range(start_y+1, start_y+sum_height+1, label.size[1]+GUIDE_WIDTH):
        draw.line([(0, y), (sheet.size[0]-1, y)], fill=grid_color,
                  width=GUIDE_WIDTH)
    for x in range(start_x+1, start_x+sum_width+1, label.size[0]+GUIDE_WIDTH):
        draw.line([(x, 0), (x, sheet.size[1]-1)], fill=grid_color,
                  width=GUIDE_WIDTH)

    # Place labels on sheet
    for x in range(start_x+GUIDE_WIDTH, start_x+sum_width, label.size[0]+GUIDE_WIDTH):
        for y in range(start_y+GUIDE_WIDTH, start_y+sum_height, label.size[1]+GUIDE_WIDTH):
            sheet.paste(label, box=(x,y))


    sheet.save(args.outputfile)

def parse_args():
    parser = argparse.ArgumentParser(description='Tile beer labels on A4 pages')
    parser.add_argument('-l', metavar='loglevel', type=str,
                        dest='loglevel', choices=logging._levelToName.values(),
                        default='WARNING',
                        help='The log level to use')
    parser.add_argument('inputfile', metavar='LABELFILE', type=str,
                        help='The image file containing the beer label')
    parser.add_argument('outputfile', metavar='OUTPUTFILE', type=str,
                        help='The file to write the resulting sheet to')
    return parser.parse_args()

def all_pixels(image):
    """Yields all RGB triplets from an image (alpha channel is excluded)"""
    pixels = image.load()
    width, height = image.size
    for x in range(0, width):
        for y in range(0, height):
            yield pixels[x,y][:3]

def most_common_color(image):
    counter = Counter(all_pixels(image))
    color, count = counter.most_common(1)[0]
    return color

def calculate_grid_color(image):
    """
    Calculates a grid color by getting the most common color in the image and
    lightening it slightly

    """
    common = most_common_color(image)
    _logger.debug("grid: Most common color in label: %s", common)
    hls = colorsys.rgb_to_hls(*[c/255 for c in common])
    _logger.debug("grid: HLS conversion: %s", hls)
    lightness = hls[1] * LIGHTNESS_FACTOR
    hls = (hls[0], lightness, hls[2])
    _logger.debug("grid: Modified HLS: %s", hls)
    grid_color = tuple(round(i*255) for i in colorsys.hls_to_rgb(*hls))
    _logger.debug("grid: Resulting RGB: %s", grid_color)
    return grid_color


if __name__ == '__main__':
    main()
