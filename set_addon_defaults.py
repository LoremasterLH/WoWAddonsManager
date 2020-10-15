import logging
import os
import re
import shutil


def load_lua(filename: str) -> str:
    with open(filename, 'r') as file:
        return file.read()


def save_lua(filename: str, data: str) -> None:
    with open(filename, 'w') as file:
        file.write(data)


logging.basicConfig(level=logging.INFO, format='')

root = 'C:/Igre/World of Warcraft/_retail_/WTF/Account/12TUZLA21/'

for subdir, dirs, files in os.walk(root):
    # print(files)
    if 'layout-local.txt' in files:
        shutil.copy('defaults/layout-local.txt', f'{subdir}/layout-local.txt')

        if 'AddOns.txt' not in files:
            shutil.copy('groups/Default.txt', f'{subdir}/AddOns.txt')
            shutil.copy('defaults/config-cache.wtf', f'{subdir}/config-cache.wtf')
            logging.info(f'Added addons and config-cache.wtf files to {subdir}')

        # Set location of WoWHead button
        # data = load_lua(f'{subdir}/SavedVariables/+Wowhead_Looter.lua')
        # wowhead_minimap = re.findall(r'wlSetting\s*=\s*{[^}]+}', data)[0]
        # save_lua(f'{subdir}/SavedVariables/+Wowhead_Looter.lua', data.replace(wowhead_minimap, 'wlSetting = {\n\t["minimapPos"] = 152,\n}'))

        try:
            data = load_lua(f'{subdir}/SavedVariables/Scrap.lua')
            # config = ConfigParser()
            # print(data)
            # config.read_string(f'[DEFAULT]\n{data}')
            if len(re.findall(r'\["share"\]', data)) == 0:  # If there's no "share" entry, we have to add it
                share_loc = re.findall('Scrap_CharSets = {', data)[0]
                save_lua(f'{subdir}/SavedVariables/Scrap.lua', data.replace(share_loc, 'Scrap_CharSets = {\n\t["share"] = true,'))
                logging.info(f'Replace Scrap.lua for {subdir}')
        except FileNotFoundError:
            shutil.copy('defaults/Scrap.lua', f'{subdir}/SavedVariables/Scrap.lua')

        logging.info(f'Reset layout for {subdir}.')
