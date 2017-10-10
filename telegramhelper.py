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


xldoc = docExtractor("SWITCH.xlsx", sheet_index=0)
print(xldoc)


def stringery(ls):
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
    print(menu)
    return menu


regularButtonsMenu([1, 2, 3, 4, 5, 10, 12, 99, 0, 50, 6, 7], 2)
regularButtonsMenu(["pouya", "parham", "samad", "mohammad",
                    "zahra", "mahshid", "mohsen", "vajihe"], 3)


# Similarity function for finding the button in case of typos
def similarity(sourceset, sample):
    seq = list()
    sourcelist = list(sourceset)
    for elem in sourceset:
        seq.append(SequenceMatcher(a=sample, b=elem))
    ratios = [st.ratio() for st in seq]
    print(ratios)
    return sourcelist[ratios.index(max(ratios))]


print(similarity({"pouya", "parham", "hassan", "mohammad"}, sample="pourya"))
