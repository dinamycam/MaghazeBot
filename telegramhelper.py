from telegram import KeyboardButton
import logging
import xlrd
from difflib import *

logger = logging.getLogger(__name__)


def docExtractor(filename, sheet_index=0):
    openbook = xlrd.open_workbook(filename)
    opensheet = openbook.sheet_by_index(sheet_index)

    documentlist = list()

    for rw in range(opensheet.nrows):
        for cl in range(opensheet.ncols):
            documentlist.append(str(opensheet.cell_value(rowx=rw, colx=cl)))
        documentlist.append('\n')
    return ' '.join(documentlist)


def stringery(ls):
    # TODO: keyboard buttons built using strings are really big.
    # should try and use the KeyboardButton type.
    if ls == []:
        return []
    return [str(ls[0])] + stringery(ls[1:])


def regularButtonsMenu(buttons,
                       n_cols,
                       header_buttons=None,
                       footer_buttons=None):
    buttons = stringery(buttons)
    print(buttons)
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    logger.debug("buttons created")
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    logger.debug("header and footer buttons added")
    # print(menu)
    return menu


# Similarity function for finding the button in case of typos
def similarity(sourceset, sample):
    seq = list()
    sourcelist = list(sourceset)
    for elem in sourceset:
        seq.append(SequenceMatcher(a=sample, b=elem))
    ratios = [st.ratio() for st in seq]
    # print(ratios)
    return sourcelist[ratios.index(max(ratios))]


def utf_decode(dataset):
    processed_list = list()
    for el in dataset:
        processed_list.append(el.decode("utf-8"))
    return processed_list


if __name__ == '__main__':
    # import os
    # os.chdir('./data')
    # xldoc = docExtractor("wires.xlsx", sheet_index=0)
    # os.chdir('..')
    # print(xldoc)

    regularButtonsMenu([1, 2, 3, 4, 5, 10, 12, 99, 0, 50, 6, 7], 2)
    regularButtonsMenu(["pouya", "parham", "samad", "mohammad",
                        "zahra", "mahshid", "mohsen", "vajihe"], 3)

    print(similarity(
        {"pouya", "parham", "hassan", "mohammad"}, sample="pourya"))
