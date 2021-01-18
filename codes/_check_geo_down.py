def plot_map(phase='train', refined=False, limited=None, sort_std=False):
    import colorsys
    import folium
    import numpy as np
    from mmm import DataHandler as DH
    from geodown_training import limited_category

    input_path = '../datas/geo_down/inputs/'
    datas = DH.loadPickle('geo_down_train.pickle', input_path)
    category = DH.loadJson('category.json', input_path)
    mean, std = DH.loadNpy('normalize_params.npy', input_path)
    # -------------------------------------------------------------------------
    # rep_category = {'lasvegas': 0, 'newyorkcity': 1, 'seattle': 2}
    # category = limited_category(rep_category)
    category = list(category.keys())
    # class_num = len(category)

    if sort_std:
        groups = {key: [] for key in category}
        for item in datas:
            for label in item['labels']:
                groups[category[label]].append(item['locate'])

        stds = [
            (idx, np.std(val)) for idx, (_, val) in enumerate(groups.items())
        ]
        stds.sort(key=lambda x: x[1])
        stds = [(key, idx, val) for idx, (key, val) in enumerate(stds)]
        stds.sort(key=lambda x: x[0])

    _map = folium.Map(
        location=[40.0, -100.0],
        zoom_start=4,
        tiles='Stamen Terrain'
    )

    limited = category[:] if limited is None else limited
    limited = set(limited) & set(category)
    convert_idx = {}
    cnt = 0
    for idx, cat in enumerate(category):
        if cat in limited:
            convert_idx[idx] = cnt
            cnt += 1

    color_num = len(convert_idx)
    HSV_tuples = [(x * 1.0 / color_num, 1.0, 1.0) for x in range(color_num)]
    RGB_tuples = [
        '#%02x%02x%02x' % (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255))
        for x in list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))
    ]

    for item in datas:
        labels, locate = item['labels'], item['locate']
        locate = [locate[1], locate[0]]
        radius = 150
        for lbl in labels:
            popup = category[lbl]
            if popup not in limited:
                continue

            if sort_std:
                lbl = stds[lbl][1]

            folium.Circle(
                radius=radius,
                location=locate,
                popup=popup,
                color=RGB_tuples[convert_idx[lbl]],
                fill=False,
            ).add_to(_map)
            radius *= 2

    return _map


def visualize_classmap(weight='../datas/geo_down/outputs/learned/000weight.pth',
                       lat_range=(25, 50), lng_range=(-60, -125), unit=0.5,
                       limited=None):
    import colorsys
    import folium
    import numpy as np
    import torch
    from mmm import CustomizedMultiLabelSoftMarginLoss as MyLossFunction
    from mmm import GeotagGCN
    from geodown_training import limited_category

    # -------------------------------------------------------------------------
    # load classifier
    from mmm import DataHandler as DH
    category = DH.loadJson('category.json', '../datas/geo_rep/inputs')
    mean, std = DH.loadNpy('normalize_params.npy', '../datas/geo_rep/inputs')
    # -------------------------------------------------------------------------

    rep_category = {'lasvegas': 0, 'newyorkcity': 1}
    # category = limited_category(rep_category)
    category = {'bellagio': 0, 'grandcentralstation': 1, 'lasvegas': 2,
                'newyorkcity': 3}
    num_class = len(category)

    gcn_settings = {
        'category': category,
        'rep_category': rep_category,
        'filepaths': {
            'relationship': '../datas/bases/geo_relationship.pickle',
            'learned_weight': '../datas/geo_rep/outputs/learned_small/010weight.pth'
            # 'learned_weight': input_path + '200weight.pth'
        },
        'feature_dimension': 30,
        'simplegeonet_settings': {
            'class_num': len(rep_category), 'mean': mean, 'std': std
        }
    }

    model = GeotagGCN(
        class_num=num_class,
        loss_function=MyLossFunction(reduction='none'),
        weight_decay=1e-4,
        network_setting=gcn_settings,
    )
    model.loadmodel(weight)

    # -------------------------------------------------------------------------
    # make points
    lat_range, lng_range = sorted(lat_range), sorted(lng_range)
    lats = np.arange(lat_range[0], lat_range[1], unit)
    lngs = np.arange(lng_range[0], lng_range[1], unit)

    # -------------------------------------------------------------------------
    # make base map
    _map = folium.Map(
        location=[40.0, -100.0],
        zoom_start=4,
        tiles='Stamen Terrain'
    )

    # make colors list
    limited = category[:] if limited is None else limited
    limited = set(limited) & set(category)
    convert_idx = {}
    cnt = 0
    for idx, cat in enumerate(category):
        if cat in limited:
            convert_idx[idx] = cnt
            cnt += 1

    color_num = len(convert_idx)
    HSV_tuples = [(x * 1.0 / color_num, 1.0, 1.0) for x in range(color_num)]
    # HSV_tuples = [(x * 1.0 / num_class, 1.0, 1.0) for x in range(num_class)]
    RGB_tuples = [
        '#%02x%02x%02x' % (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255))
        for x in list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))
    ]

    # -------------------------------------------------------------------------
    # plot
    category = list(category.keys())
    for lat in lats:
        for lng in lngs:
            # labels = model.predict(torch.Tensor([30, -80]), labeling=True)
            labels = model.predict(torch.Tensor([lng, lat]), labeling=True)
            labels = np.where(labels[0] > 0)[0]
            radius = 150
            for lbl in labels:
                popup = category[lbl]
                if popup not in limited:
                    continue

                folium.Circle(
                    radius=radius,
                    location=[lat, lng],
                    popup=popup,
                    color=RGB_tuples[convert_idx[lbl]],
                    fill=False
                ).add_to(_map)
                radius *= 2

    # datas = DH.loadPickle('geo_down_train.pickle', '../datas/geo_down/inputs/')
    # for item in datas:
    #     loc = item['locate']
    #     # labels = model.predict(torch.Tensor([[lng, lat]]), labeling=True)
    #     labels = model.predict(torch.Tensor([loc]), labeling=False)
    #     labels = np.where(labels[0] > 0)[0]
    #     radius = 150
    #     for lbl in labels:
    #         popup = category[lbl]
    #         if popup not in limited:
    #             continue

    #         folium.Circle(
    #             radius=radius,
    #             location=[loc[1], loc[0]],
    #             popup=popup,
    #             color=RGB_tuples[convert_idx[lbl]],
    #             fill=False
    #         ).add_to(_map)
    #         radius *= 2

    return _map


def visualize_training_data(tag, phase='train', limited=[-1, 0, 1]):
    '''
    あるクラスについて学習データを正例(1)・unknown(-1)・負例(0)に振り分けプロット
    '''
    import colorsys
    import folium
    import numpy as np
    import torch
    from geodown_training import limited_category
    # from mmm import DataHandler as DH
    from mmm import DatasetGeotag
    from mmm import GeoUtils as GU
    from tqdm import tqdm

    # -------------------------------------------------------------------------
    # データの読み込み
    input_path = '../datas/geo_down/inputs/'
    # rep_category = DH.loadJson('upper_category.json', input_path)
    # category = DH.loadJson('category.json', input_path)
    rep_category = {'lasvegas': 0, 'newyorkcity': 1, 'seattle': 2}
    category = limited_category(rep_category)
    num_class = len(category)
    if tag not in category:
        raise Exception
    tag_idx = category[tag]

    kwargs_DF = {
        'train': {
            'class_num': num_class,
            'transform': torch.tensor,
            'data_path': input_path + 'geo_down_train.pickle'
        },
        'validate': {
            'class_num': num_class,
            'transform': torch.tensor,
            'data_path': input_path + 'geo_down_validate.pickle'
        },
    }

    dataset = DatasetGeotag(**kwargs_DF[phase])
    loader = torch.utils.data.DataLoader(
        dataset,
        shuffle=False,
        batch_size=1,
        num_workers=4
    )

    mask = GU.down_mask(rep_category, category, sim_thr=5, saved=False)

    # -------------------------------------------------------------------------
    def _fixed_mask(labels, fmask):
        '''
        誤差を伝播させない部分を指定するマスクの生成
        '''
        labels = labels.data.cpu().numpy()
        labels_y, labels_x = np.where(labels == 1)
        labels_y = np.append(labels_y, labels_y[-1] + 1)
        labels_x = np.append(labels_x, 0)

        fixmask = np.zeros((labels.shape[0] + 1, labels.shape[1]), int)
        row_p, columns_p = labels_y[0], [labels_x[0]]
        fixmask[row_p] = fmask[labels_x[0]]

        for row, column in zip(labels_y[1:], labels_x[1:]):
            if row == row_p:
                columns_p.append(column)
            else:
                if len(columns_p) > 1:
                    for x in columns_p:
                        fixmask[row_p][x] = 0

                row_p, columns_p = row, [column]

            fixmask[row] = fixmask[row] | fmask[column]

        fixmask = fixmask[:-1]

        return fixmask

    # -------------------------------------------------------------------------
    # トレーニングデータを振り分け
    loc_ans_list = []
    for locate, label, _ in tqdm(loader):
        fix_mask = _fixed_mask(label, mask)
        locate = (float(locate[0][0]), float(locate[0][1]))
        flg = -1 if fix_mask[0][tag_idx] == 1 else 0 \
            if label[0][tag_idx] == 0 else 1

        loc_ans_list.append((locate, flg))

    # -------------------------------------------------------------------------
    # plot
    color_num = 3
    HSV_tuples = [(x * 1.0 / color_num, 1.0, 1.0) for x in range(color_num)]
    RGB_tuples = [
        '#%02x%02x%02x' % (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255))
        for x in list(map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples))
    ]

    _map = folium.Map(
        location=[40.0, -100.0],
        zoom_start=4,
        tiles='Stamen Terrain'
    )

    print('plotting...')
    for locate, label in tqdm(loc_ans_list):
        if label not in limited:
            continue

        locate = [locate[1], locate[0]]
        folium.Circle(
            radius=150,
            location=locate,
            popup=label,
            color=RGB_tuples[label],
            fill=False,
        ).add_to(_map)

    return _map


def confusion_all_matrix(epoch=20, saved=True,
                         weight_path='../datas/geo_down/outputs/learned/',
                         outputs_path='../datas/geo_down/outputs/check/'):
    '''
    正例・unknown・負例についてconfusion_matrixを作成
    '''
    # -------------------------------------------------------------------------
    # 準備
    import numpy as np
    import os
    import torch
    from geodown_training import limited_category
    from mmm import DataHandler as DH
    from mmm import DatasetGeotag
    from mmm import GeotagGCN
    from mmm import GeoUtils as GU
    from tqdm import tqdm

    os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    # データの読み込み先
    base_path = '../datas/bases/'
    input_path = '../datas/geo_down/inputs/'

    rep_category = DH.loadJson('upper_category.json', input_path)
    category = DH.loadJson('category.json', input_path)
    rep_category = {'lasvegas': 0, 'newyorkcity': 1, 'seattle': 2}
    # category = limited_category(rep_category)
    category = limited_category(
        rep_category,
        lda='../datas/geo_down/inputs/local_df_area16_wocoth_new'
    )
    num_class = len(category)

    geo_down_train = GU.down_dataset(
        rep_category, category, 'train',
        base_path=base_path
        # base_path=input_path
    )
    geo_down_validate = GU.down_dataset(
        rep_category, category, 'validate',
        base_path=base_path
        # base_path=input_path
    )
    DH.savePickle(geo_down_train, 'geo_down_train', input_path)
    DH.savePickle(geo_down_validate, 'geo_down_validate', input_path)

    kwargs_DF = {
        'train': {
            'class_num': num_class,
            'transform': torch.tensor,
            'data_path': input_path + 'geo_down_train.pickle'
        },
        'validate': {
            'class_num': num_class,
            'transform': torch.tensor,
            'data_path': input_path + 'geo_down_validate.pickle'
        },
    }

    train_dataset = DatasetGeotag(**kwargs_DF['train'])
    val_dataset = DatasetGeotag(**kwargs_DF['validate'])

    # maskの読み込み
    mask = GU.down_mask(rep_category, category, saved=False)

    # 入力位置情報の正規化のためのパラメータ読み込み
    mean, std = DH.loadNpy('normalize_params', input_path)

    # 学習で用いるデータの設定や読み込み先
    gcn_settings = {
        'category': category,
        'rep_category': rep_category,
        'filepaths': {
            'relationship': base_path + 'geo_relationship.pickle',
            'learned_weight': input_path + '020weight.pth'
            # 'learned_weight': input_path + '200weight.pth'
        },
        'feature_dimension': 30,
        'simplegeonet_settings': {
            'class_num': len(rep_category), 'mean': mean, 'std': std
        }
    }

    # modelの設定
    model = GeotagGCN(
        class_num=num_class,
        learningrate=0.1,
        momentum=0.9,
        weight_decay=1e-4,
        fix_mask=mask,
        network_setting=gcn_settings,
        multigpu=False,
    )
    if epoch > 0:
        model.loadmodel('{0:0=3}weight'.format(epoch), weight_path)

    def _update_backprop_weight(labels, fmask):
        '''
        誤差を伝播させる際の重みを指定．誤差を伝播させない部分は0．
        '''
        labels = labels.data.cpu().numpy()
        labels_y, labels_x = np.where(labels == 1)
        labels_y = np.append(labels_y, labels_y[-1] + 1)
        labels_x = np.append(labels_x, 0)

        weight = np.zeros((labels.shape[0] + 1, labels.shape[1]), int)
        row_p, columns_p = labels_y[0], [labels_x[0]]
        weight[row_p] = fmask[labels_x[0]]

        for row, column in zip(labels_y[1:], labels_x[1:]):
            if row == row_p:
                columns_p.append(column)
            else:
                if len(columns_p) > 1:
                    for y in columns_p:
                        weight[row_p][y] = 0

                row_p, columns_p = row, [column]

            weight[row] = weight[row] | fmask[column]

        weight = weight[:-1]
        weight = np.ones(labels.shape, int) - weight

        return weight

    # ---入力画像のタグから振り分け-----------------------------------------------
    # 0: precision, 1: recall, 2: positive_1, 3: positive_all,
    # 4: unknown_1, 5: unknown_all, 6: negative_1, 7: negative_all

    def count_result(dataset):
        from mmm import MakeBPWeight

        loader = torch.utils.data.DataLoader(
            dataset,
            shuffle=True,
            batch_size=1,
            num_workers=4
        )
        bp_weight = MakeBPWeight(dataset, len(category), mask)

        allnum = 0
        counts = np.zeros((len(category), 8))
        for locate, label, _ in tqdm(loader):
            allnum += 1
            fix_mask = _update_backprop_weight(label, mask)
            predicts = model.predict(locate, labeling=True)
            for idx, flg in enumerate(fix_mask[0]):
                # あるクラスcategory[idx]について
                if flg == 0:
                    # 正解がunknownのとき
                    if predicts[0][idx] == 1:
                        # 予測が1であれば
                        counts[idx][4] += 1

                    continue

                if label[0][idx] == 0:
                    # 正解が0のとき
                    if predicts[0][idx] == 1:
                        # 予測が1であれば
                        counts[idx][6] += 1
                else:
                    # 正解が1のとき
                    if predicts[0][idx] == 1:
                        # 予測が1であれば
                        counts[idx][2] += 1

        for idx, (zero, one) in enumerate(bp_weight):
            counts[idx][3] = one
            counts[idx][5] = allnum - one - zero
            counts[idx][7] = zero

            if counts[idx][2] + counts[idx][6] != 0:
                counts[idx][0] = counts[idx][2] / (counts[idx][2] + counts[idx][6])
            if counts[idx][3] != 0:
                counts[idx][1] = counts[idx][2] / counts[idx][3]

        return counts

    train_counts = count_result(train_dataset)
    validate_counts = count_result(val_dataset)

    if saved:
        DH.saveNpy(
            np.array(train_counts),
            'cm_train_{0:0=3}'.format(epoch),
            outputs_path
        )
        DH.saveNpy(
            np.array(validate_counts),
            'cm_validate_{0:0=3}'.format(epoch),
            outputs_path
        )

    return np.array(train_counts), np.array(validate_counts)


if __name__ == "__main__":
    confusion_all_matrix(
        epoch=0,
        weight_path='../datas/geo_down/outputs/learned_basic_bp/',
        outputs_path='../datas/geo_down/outputs/check/basic_bp/'
    )
    # visualize_classmap()
    # plot_map()
    # visualize_training_data('bellagio')

    print('finish.')
