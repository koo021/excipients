import streamlit as st
import json
import zipfile
from io import BytesIO
import re
import os
import time  # Added for timestamp

# Define all excipient types from the provided text
excipient_types = [
    '稀释剂',
    '黏合剂',
    '崩解剂',
    '润滑剂',
    '助流剂或抗结块剂',
    '包衣剂',
    '增塑剂',
    '表面活性剂',
    '释放调节剂',
    '压敏胶黏剂'
]

# Common sub-properties (1.1 to 1.4)
sub_properties = [
    "1.1 辅料名称 (Excipient name)",
    "1.2 CAS号 (CAS Number)",
    "1.3 所测试辅料厂家 (Tested Manufacturer)",
    "1.4 辅料厂家规格 (Manufacturer Specification)"
]

# Physicochemical properties for each type, including descriptions from the text
phys_properties = {
    '稀释剂': [
        "酸碱度 (pH): 在一定程度上决定制剂的制备工艺，同时可能影响药物的稳定性",
        "解离度 (Dissociation degree): 在一定程度上影响药物的溶出",
        "氧化还原性 (Oxidation-reduction property): 与原料及辅料间相容性有关",
        "粒度和粒度分布 (Particle size and distribution): 影响粉末的流动性、含量均匀度及溶出度等",
        "粒子形态 (Particle morphology): 影响制剂压制后粒子间相互作用，进而影响药物溶出",
        "堆密度、振实密度、真密度 (Bulk density, tapped density, true density): 是评价辅料流动性、可压性的关键指标",
        "比表面积 (Specific surface area): 在一定程度上体现辅料的粒度、形貌、多孔性等",
        "结晶性 (Crystallinity): 影响稀释剂流动性及溶解性",
        "水分 (Moisture): 可能影响片剂的硬度、崩解性、溶出度等",
        "流动性 (Flowability): 对于直压型处方可能影响含量均匀性",
        "溶解度 (Solubility): 在介质中的溶解度可能影响制剂的溶出度",
        "晶型 (Polymorph): 其转变可能影响稳定性",
        "可压性 (Compressibility): 影响片剂的硬度、脆碎度等"
    ],
    '黏合剂': [
        "表面张力 (Surface tension): 影响润湿物料所需加入的黏合剂用量",
        "粒度和粒度分布 (Particle size and distribution): 影响黏合剂与干混合物均匀混合",
        "溶解度 (Solubility): 与润湿剂的选择有关",
        "黏度 (Viscosity): 与功能直接相关",
        "分子量和分子量分布 (Molecular weight and distribution): 聚合物的分子量与黏度相关"
    ],
    '崩解剂': [
        "粒度和粒度分布 (Particle size and distribution): 崩解力与崩解程度都与崩解剂的粒径有关",
        "吸水速率 (Water absorption rate): 崩解剂的水吸收速率越高崩解越快",
        "膨胀率或膨胀指数 (Swelling rate or index): 能产生显著膨胀力的崩解剂一般更为有效",
        "接触液体后的形态 (Morphology after liquid contact): 最终崩解剂是微粒态或是凝胶态均影响崩解效果",
        "水分 (Moisture): 淀粉等作崩解剂时，水分对其崩解性能影响显著",
        "泡腾量 (Effervescence amount): 影响泡腾崩解剂的性质"
    ],
    '润滑剂': [
        "粒度 (Particle size): 粉体的基本特性",
        "比表面积 (Specific surface area): 润滑剂的作用效果与其比表面积有关",
        "水合情况 (Hydration status): 如硬脂酸镁吸水后可生成多种水合物",
        "多晶型 (Polymorphism): 界面润滑剂由晶体组成",
        "纯度 (Purity): 如硬脂酸镁的组成中硬脂酸盐与棕榈酸盐的比率",
        "水分 (Moisture): 含水量会影响润滑作用"
    ],
    '助流剂或抗结块剂': [
        "粒度和粒度分布 (Particle size and distribution): 基本理化性质",
        "比表面积 (Specific surface area): 助流效果与其比表面积有关，粒度越细比表面积越大",
        "水分 (Moisture): 它们可能具有轻微的引湿性"
    ],
    '包衣剂': [
        "组成、结构和纯度 (Composition, structure, and purity): 基本化学性质",
        "分子量及其分布 (Molecular weight and distribution): 影响功能",
        "表观黏度 (Apparent viscosity): 物理性质",
        "玻璃化转变温度 (Tg) (Glass transition temperature): 影响表观黏度的因素",
        "黏度 (Viscosity): 对于水分散体",
        "表面张力 (Surface tension): 对于水分散体"
    ],
    '增塑剂': [
        "溶解性 (Solubility): 水溶性和脂溶性两大类",
        "熔点 (Melting point): 增塑剂通常熔点较低（<100℃）"
    ],
    '表面活性剂': [
        "表面张力 (Surface tension): 用于描述降低界面张力的能力",
        "临界胶束浓度 (CMC) (Critical micelle concentration): 一定温度下表面活性剂在溶液中的特定浓度",
        "润湿性 (Wettability): 用接触角度量的性质，用于评价液体对固体表面的润湿能力",
        "亲水亲油平衡值 (HLB) (Hydrophilic-lipophilic balance): 不同HLB值的表面活性剂有其各自独特的用途",
        "昙点 (Cloud point): 当温度达到昙点时，非离子型表面活性剂与溶液间的氢键断裂",
        "Krafft点 (Krafft point): 当温度达到Krafft点时，离子型表面活性剂的溶解性急剧增加"
    ],
    '释放调节剂': [
        "化学组成 (Chemical composition): 共聚物和纤维素衍生物的化学组成",
        "离子化程度 (Ionization degree): 化学性质",
        "分子量 (Molecular weight): 化学性质",
        "交联度 (Crosslinking degree): 化学性质",
        "脂肪酸组成 (Fatty acid composition): 对于脂质聚合物",
        "凝胶点 (Gel point): 亲水性聚合物的物理特性",
        "凝胶强度 (Gel strength): 亲水性聚合物的物理特性",
        "黏弹性特性 (Viscoelastic properties): 亲水性聚合物的物理特性",
        "溶解度 (Solubility): 疏水性聚合物的物理特性",
        "成膜性 (Film-forming property): 疏水性聚合物的物理特性",
        "熔点 (Melting point): 疏水性脂质材料的物理特性"
    ],
    '压敏胶黏剂': [
        "黏性和黏弹性 (Adhesiveness and viscoelasticity): 影响制剂的初粘力、持粘力、剥离力等",
        "分子量及分子量分布 (Molecular weight and distribution): 对每批压敏胶黏剂性能的重现性至关重要"
    ]
}

fixed_json_filename = '辅料_functional_standards.json'

def sanitize_filename(s):
    return re.sub(r'[\\/:*?"<>|]', '_', s)

def create_docx(data):
    mem_zip = BytesIO()

    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types)

        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels)

        doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
</Relationships>'''
        zf.writestr('word/_rels/document.xml.rels', doc_rels)

        paragraphs = []
        for key, value in data.items():
            if isinstance(value, dict):
                paragraphs.append(f"{key}:")
                if key == "1.6 模型片测试结果 (Model Tablet Test Results)":
                    paragraphs.append(f"  模型片名称: {value.get('模型片名称', '')}")
                    paragraphs.append(f"  原研厂家: {value.get('原研厂家', '')}")
                    for indicator in value.get('评价指标', []):
                        paragraphs.append(f"  评价指标: {indicator.get('指标名称', '')}")
                        paragraphs.append(f"    原研结果: {indicator.get('原研结果', '')}")
                        paragraphs.append(f"    本辅料结果: {indicator.get('本辅料结果', '')}")
                        paragraphs.append(f"    结果技术阐释: {indicator.get('结果技术阐释', '')}")
                        for other in indicator.get('其他厂家结果', []):
                            paragraphs.append(f"    其他厂家: {other.get('厂家名称', '')}")
                            paragraphs.append(f"      辅料规格: {other.get('辅料规格', '')}")
                            paragraphs.append(f"      结果: {other.get('结果', '')}")
                else:
                    for sub_key, sub_value in value.items():
                        paragraphs.append(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                paragraphs.append(f"{key}:")
                for item in value:
                    paragraphs.append(f"  - {item}")
            else:
                paragraphs.append(f"{key}: {value}")

        body_content = ''.join([f'<w:p><w:r><w:t>{p}</w:t></w:r></w:p>' for p in paragraphs if p])

        document = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        {body_content}
        <w:sectPr>
            <w:pgSz w:w="12240" w:h="15840"/>
            <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
            <w:cols w:space="720"/>
            <w:docGrid w:linePitch="360"/>
        </w:sectPr>
    </w:body>
</w:document>'''
        zf.writestr('word/document.xml', document)

    mem_zip.seek(0)
    return mem_zip

st.title("辅料功能标准收集器 (Excipient Functional Standards Collector)")

st.markdown("""
选择辅料类型，然后输入每个分类属性的相关数据（按照eCTD Module 3.2.P.4格式收集）。1.5下为物料化学指标的子项，会根据类型变化。已覆盖所有口服固体制剂辅料类型。可选择是否生成Word文档。所有数据保存在单一JSON文件'辅料_functional_standards.json'中，不会覆盖；Word根据厂家规格命名。填写辅料名称后可加载现有数据。
""")

selected_type = st.selectbox("辅料类型 (Excipient Type)", excipient_types, key="selected_type")

st.header(f"1. {selected_type}功能标准")

# Sub properties with keys
sub_data = {}
for prop in sub_properties:
    prop_name = prop.split(':')[0].strip()
    key = f"sub_{prop_name.replace(' ', '_')}"
    sub_data[prop_name] = st.text_input(prop, key=key)

# 1.5 Physicochemical properties with keys
st.subheader("1.5 物料化学指标 (Material Chemical Indicators)")
phys_data = {}
for prop in phys_properties[selected_type]:
    prop_name = prop.split(':')[0].strip()
    key = f"phys_{prop_name.replace(' ', '_')}"
    phys_data[prop_name] = st.text_input(prop, key=key)

# 1.6 Test results - dynamic indicators with keys
st.subheader("1.6 模型片测试结果 (Model Tablet Test Results)")
model_tablet_name = st.text_input("模型片名称 (Model Tablet Name)", key="model_tablet_name")
original_manufacturer = st.text_input("原研厂家 (Original Manufacturer)", key="original_manufacturer")

if "num_indicators" not in st.session_state:
    st.session_state.num_indicators = 1

if st.button("添加评价指标 (Add Indicator)"):
    st.session_state.num_indicators += 1

indicators = []
for i in range(st.session_state.num_indicators):
    st.markdown(f"**评价指标 {i+1}**")
    indicator_name = st.text_input(f"指标名称 {i+1} (e.g., 硬度)", key=f"indicator_name_{i}")
    original_result = st.text_input(f"原研结果 {i+1}", key=f"original_result_{i}")
    this_result = st.text_input(f"本辅料结果 {i+1}", key=f"this_result_{i}")
    technical_explanation = st.text_input(f"结果技术阐释 {i+1}", key=f"technical_explanation_{i}")
    
    other_results = []
    for j in range(2):  # Allow up to 2 other manufacturers
        st.markdown(f"**其他厂家 {j+1}**")
        other_manufacturer_name = st.text_input(f"厂家名称 {i+1}-{j+1}", key=f"other_manufacturer_name_{i}_{j}")
        other_spec = st.text_input(f"辅料规格 {i+1}-{j+1}", key=f"other_spec_{i}_{j}")
        other_result = st.text_input(f"结果 {i+1}-{j+1}", key=f"other_result_{i}_{j}")
        if other_manufacturer_name or other_spec or other_result:
            other_results.append({
                "厂家名称": other_manufacturer_name,
                "辅料规格": other_spec,
                "结果": other_result
            })
    
    if indicator_name:
        indicators.append({
            "指标名称": indicator_name,
            "原研结果": original_result,
            "本辅料结果": this_result,
            "结果技术阐释": technical_explanation,
            "其他厂家结果": other_results
        })

generate_word = st.checkbox("生成Word文档 (Generate Word Document)")

if st.button("保存为eCTD格式 (Save to eCTD Format)"):
    data = {"功能类型 (Excipient Type)": selected_type}
    data.update(sub_data)
    data["1.5 物料化学指标 (Material Chemical Indicators)"] = phys_data
    data["1.6 模型片测试结果 (Model Tablet Test Results)"] = {
        "模型片名称": model_tablet_name,
        "原研厂家": original_manufacturer,
        "评价指标": indicators
    }
    
    excipient_name = sanitize_filename(sub_data["1.1 辅料名称 (Excipient name)"])
    manufacturer_spec = sanitize_filename(sub_data["1.4 辅料厂家规格 (Manufacturer Specification)"])
    
    if not excipient_name:
        st.warning("请填写辅料名称以保存JSON文件。")
    else:
        # Generate unique key with timestamp to avoid overwrite
        timestamp = int(time.time())
        key = f'{selected_type}_{excipient_name}_{timestamp}'
        
        all_data = {}
        if os.path.exists(fixed_json_filename):
            with open(fixed_json_filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        
        # Simulate eCTD structure
        justifications = {}
        for i, prop in enumerate(sub_properties):
            justifications[prop.split(':')[0].strip()] = "" if len(prop.split(':')) == 1 else prop.split(':')[1].strip()
        for prop in phys_properties[selected_type]:
            justifications[f"1.5.{prop.split(':')[0].strip()}"] = prop.split(':')[1].strip()
        for i in range(len(indicators)):
            justifications[f"1.6.评价指标 {i+1}"] = ""
        
        ectd_data = {
            "3.2.P.4 Control of Excipients": {
                "3.2.P.4.1 Specifications": data,
                "3.2.P.4.4 Justification of Specifications": justifications
            }
        }
        
        all_data[key] = ectd_data
        
        with open(fixed_json_filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        
        st.success(f"Data saved to {fixed_json_filename} under key '{key}'.")
        
        if generate_word:
            if not manufacturer_spec:
                manufacturer_spec = excipient_name if excipient_name else "default"
            docx_filename = f'{selected_type}_{manufacturer_spec}_functional_standards.docx'
            docx_bytes = create_docx(data)
            st.download_button("下载Word文档", docx_bytes.getvalue(), file_name=docx_filename, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.success(f"Word document ready for download as {docx_filename}.")

if st.button("加载现有数据 (Load Existing Data)"):
    excipient_name = sanitize_filename(sub_data["1.1 辅料名称 (Excipient name)"])
    if not excipient_name:
        st.warning("请先填写辅料名称以加载数据。")
    else:
        # Find the latest key matching type and name (ignoring timestamp)
        found_key = None
        latest_timestamp = 0
        if os.path.exists(fixed_json_filename):
            with open(fixed_json_filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                for k in all_data:
                    if k.startswith(f'{selected_type}_{excipient_name}_'):
                        ts = int(k.split('_')[-1])
                        if ts > latest_timestamp:
                            latest_timestamp = ts
                            found_key = k
        if found_key:
            ectd_data = all_data[found_key]
            specs = ectd_data["3.2.P.4 Control of Excipients"]["3.2.P.4.1 Specifications"]
            for prop in sub_properties:
                prop_name = prop.split(':')[0].strip()
                st.session_state[prop_name.replace(" ", "_")] = specs.get(prop_name, '')
            phys_data = specs.get("1.5 物料化学指标 (Material Chemical Indicators)", {})
            for prop in phys_properties[selected_type]:
                prop_name = prop.split(':')[0].strip()
                st.session_state[prop_name.replace(" ", "_")] = phys_data.get(prop_name, '')
            test = specs.get("1.6 模型片测试结果 (Model Tablet Test Results)", {})
            st.session_state["model_tablet_name"] = test.get("模型片名称", '')
            st.session_state["original_manufacturer"] = test.get("原研厂家", '')
            indicators_loaded = test.get("评价指标", [])
            st.session_state.num_indicators = len(indicators_loaded)
            for i, ind in enumerate(indicators_loaded):
                st.session_state[f"indicator_name_{i}"] = ind.get("指标名称", '')
                st.session_state[f"original_result_{i}"] = ind.get("原研结果", '')
                st.session_state[f"this_result_{i}"] = ind.get("本辅料结果", '')
                st.session_state[f"technical_explanation_{i}"] = ind.get("结果技术阐释", '')
                other_results_loaded = ind.get("其他厂家结果", [])
                for j in range(min(2, len(other_results_loaded))):
                    other = other_results_loaded[j]
                    st.session_state[f"other_manufacturer_name_{i}_{j}"] = other.get("厂家名称", '')
                    st.session_state[f"other_spec_{i}_{j}"] = other.get("辅料规格", '')
                    st.session_state[f"other_result_{i}_{j}"] = other.get("结果", '')
            st.experimental_rerun()  # Rerun to update inputs
            st.success(f"Data loaded from {fixed_json_filename} under key '{found_key}' (latest version)")
        else:
            st.warning(f"No data found for '{selected_type}_{excipient_name}' in {fixed_json_filename}")
