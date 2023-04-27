#! C:\Python311\python.exe
"""
Snapmaker Artisan G-Code Post Processor for PrusaSlicer
"""

import re
import sys
import os
from os import getenv
import codecs

file_input = sys.argv[1]


regex = r'(?:^; thumbnail begin \d+[x ]\d+ \d+)(?:\n|\r\n?)((?:.+(?:\n|\r\n?))+?)(?:^; thumbnail end)'

# slicer_output_name = str(getenv('SLIC3R_PP_OUTPUT_NAME'))

slicer_layer_height = getenv('SLIC3R_LAYER_HEIGHT', 0)
slicer_print_speed_sec = getenv('SLIC3R_MAX_PRINT_SPEED', 0)
slicer_nozzle_temperature = getenv('SLIC3R_TEMPERATURE',0)
slicer_nozzle_1_temperature = getenv('SLIC3R_TEMPERATURE',0)
slicer_nozzle_0_diameter = getenv('SLIC3R_NOZZLE_DIAMETER', 0)
slicer_nozzle_1_diameter = getenv('SLIC3R_NOZZLE_DIAMETER', 0)
slicer_bed_temperature = getenv('SLIC3R_BED_TEMPERATURE', 0)

slicer_nozzle_0_material = getenv('SLIC3R_FILAMENT_PRESET', 0)
slicer_nozzle_1_material = getenv('SLIC3R_FILAMENT_PRESET', 0)


def convert_thumbnail(lines):
    comments = ''
    for line in lines:
        if line.startswith(';') or line.startswith('\n'):
            comments += line
    matches = re.findall(regex, comments, re.MULTILINE)
    if len(matches) > 0:
        return 'data:image/png;base64,' + matches[-1:][0].replace('; ', '').replace('\r\n', '').replace('\n', '')
    return None

def find_estimated_time(lines):
    for line in lines:
        if line.startswith('; estimated printing time'):
            est = line[line.index('= ')+2:]  # 2d 12h 8m 58s
            tmp = {'d': 0, 'h': 0, 'm': 0, 's': 0}
            for t in 'dhms':
                if est.find(t) != -1:
                    idx = est.find(t)
                    tmp[t] = int(est[0:idx].replace(' ', ''))
                    est = est[idx+1:]
            return int(tmp['d'] * 86400
                     + tmp['h'] * 3600
                     + tmp['m'] * 60
                     + tmp['s'])

def find_length(lines):
    for line in lines:
        if line.startswith('; filament used [cm3]'):
            length = line[line.index('= ')+2:] #length in CM3
            length = float(length)
            return length
        
def find_weight(lines):
    for line in lines:
        if line.startswith('; filament used [g]'):
            weight = line[line.index('= ')+2:] #weight in g
            weight = float(weight)
            return weight
        
def find_filament(lines):
    for line in lines:
        if line.startswith('; filament_settings_id'):
            filament_type = line[line.index('= ')+2:] #filament type
            return filament_type
            
def convert_file():

    # Open the input file in ansi encoding
    with codecs.open(file_input, encoding="ansi") as input_file:
        # Read the contents of the input file
        contents = input_file.read()

    # Open the output file in UTF-8 encoding
    with codecs.open(file_input, mode="w", encoding="utf-8") as output_file:
        # Write the contents to the output file in UTF-8 encoding
        output_file.write(contents)

def main():
    with open(file_input, 'r') as f:
        gcode_lines = f.readlines()
        f.close()

    with open(file_input, 'w', newline='') as g:
        thumbnail = convert_thumbnail(gcode_lines)

        headers = (
                ';Header Start',
                '',
                ';FLAVOR:Marlin',
                ';header_type: 3dp',
                ';tool_head: dualExtruderToolheadForSM2',
                ';machine: A400',
                ';file_total_lines: {}'.format(len(gcode_lines)),
                ';estimated_time(s): {}'.format(find_estimated_time(gcode_lines)),
                ';nozzle_temperature(°C): {}'.format(slicer_nozzle_temperature),
                ';nozzle_1_temperature(°C): {}'.format(slicer_nozzle_temperature),
                ';nozzle_0_diameter(mm): {}'.format(slicer_nozzle_0_diameter),
                ';nozzle_1_diameter(mm): {}'.format(slicer_nozzle_1_diameter),
                ';build_plate_temperature(°C): {}'.format(slicer_bed_temperature),
                ';work_speed(mm/minute): {}'.format(int(slicer_print_speed_sec) * 60),
                ';layer_number: 0',
                ';layer_height: {}'.format(slicer_layer_height),                  
                ';matierial_weight: {}'.format(find_weight(gcode_lines)),
                ';matierial_length: {}'.format(find_length(gcode_lines)),             
                ';nozzle_0_matierial: {}'.format(find_filament(gcode_lines)),
                ';nozzle_1_matierial: {}'.format(find_filament(gcode_lines)),
                ';nozzle_0_material: {}'.format(find_filament(gcode_lines)),
                ';nozzle_1_material: {}'.format(find_filament(gcode_lines)),
                ';thumbnail: {}'.format(thumbnail) if thumbnail else ';',
                ';Header End',
                '',
                ';G-code for 3dp engraving',
                ''                
                )
        g.write('\n'.join(headers))
        g.writelines(gcode_lines)
        g.close()

        convert_file()

if __name__ == "__main__":
    print('Starting SMFix')
    try:
        main()
    except Exception as ex:
        print('Oops! something went wrong.' + str(ex))
        sys.exit(1)
    print('SMFix done')

