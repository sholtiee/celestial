"""Переводы тегов предметов мода (tag.item.celestial.*) — их показывают EMI/REI, а Fabric предупреждает о непереведённых (BUG-038).

Запускается последним в build_assets.sh: проходит по всем data/celestial/tags/item/*.json и падает, если для тега нет перевода в TAGS.
"""
import os

from gen_assets import DATA
from gen_story import lang_patch

TAGS = {
    'abyssal_tool_materials': ('Материалы безднового инструмента', 'Abyssal Tool Materials'),
    'etherite_tool_materials': ('Материалы эфиритового инструмента', 'Etherite Tool Materials'),
    'frost_tool_materials': ('Материалы инструмента из морозной стали', 'Frost Steel Tool Materials'),
    'light_sources': ('Источники света в руке', 'Hand-held Light Sources'),
    'repairs_abyssal_armor': ('Чинит бездновую броню', 'Repairs Abyssal Armor'),
    'repairs_etherite_armor': ('Чинит эфиритовую броню', 'Repairs Etherite Armor'),
    'repairs_frost_armor': ('Чинит броню из морозной стали', 'Repairs Frost Steel Armor'),
    'repairs_fur_armor': ('Чинит меховую одежду', 'Repairs Fur Clothing'),
    'repairs_ice_crown': ('Чинит Ледяную Корону', 'Repairs the Ice Crown'),
    'skywood_logs': ('Брёвна небесного дерева', 'Skywood Logs'),
}


def main():
    base = os.path.join(DATA, 'tags/item')
    found = sorted(os.path.relpath(os.path.join(dp, f), base)[:-5].replace(os.sep, '.')
                   for dp, _, fs in os.walk(base) for f in fs if f.endswith('.json'))
    missing = [t for t in found if t not in TAGS]
    assert not missing, f'нет перевода тегов предметов: {missing} — допиши в TAGS'
    lang_patch({f'tag.item.celestial.{k}': v for k, v in TAGS.items() if k in found})
    print('ok: переводы тегов предметов', len(found))


if __name__ == '__main__':
    main()
