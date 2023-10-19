from __init__ import *
import utils as _U
reload(_U)
import model as _M
reload(_M)
import dataset as _D
reload(_D)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
def model_inference(model, setting):
    
    model.eval()
    # iterate over test data
    sub_points = [setting.TEST.START_DATE] + [int(setting.TEST.END_DATE//1e4 * 1e4) + i*100 + 1 for i in range(4, 13, 3)] + [setting.TEST.END_DATE]

    symbol_factors = pd.DataFrame([], index=['code', 'date', 'up_factor']).T
    for m_idx in range(len(sub_points)-1):
        print(f"Inferencing: {sub_points[m_idx]} - {sub_points[m_idx+1]}")
        
        inference_dataset = _D.ImageDataSet(win_size = setting.DATASET.LOOKBACK_WIN, \
                                        start_date = sub_points[m_idx], \
                                        end_date = sub_points[m_idx+1], \
                                        mode = 'inference', \
                                        label = setting.TRAIN.LABEL, \
                                        indicators = setting.DATASET.INDICATORS, \
                                        show_volume = setting.DATASET.SHOW_VOLUME, \
                                        parallel_num=setting.DATASET.PARALLEL_NUM)
        inference_imageset = inference_dataset.generate_images(1.0)

        for id in range(len(inference_imageset)-1):
            if len(inference_imageset[id][1]) == 0: #inference_imageset[id] is data【codename,image,date】 of one code
                continue
            inference_imgs = []
            for img in inference_imageset[id][1]:
                inference_imgs.append(img[0])  # img[0] is the image matrix
            input = torch.Tensor(np.array(inference_imgs))
            input = input.to(device)
            output = model(input)[:, 1]
            up_factors = []
            for pred in output:
                up_factors.append(pred.item())
            symbol_f = pd.DataFrame([[inference_imageset[id][0] for _ in range(len(inference_imageset[id][1]))], inference_imageset[id][2], up_factors], index=['code', 'date', 'up_factor']).T
            
            symbol_factors = pd.concat([symbol_factors, symbol_f], axis=0)
            
    return symbol_factors


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Train Models via YAML files')
    parser.add_argument('setting', type=str, \
                        help='Experiment Settings, should be yaml files like those in /configs')

    args = parser.parse_args()

    with open(args.setting, 'r') as f:
        setting = _U.Dict2ObjParser(yaml.safe_load(f)).parse()

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    assert setting.MODEL in ['CNN5d', 'CNN20d'], f"Wrong Model Template: {setting.MODEL}"

    if 'factors' not in os.listdir('./'):
        os.system('mkdir factors')
    if setting.INFERENCE.FACTORS_SAVE_FILE.split('/')[1] not in os.listdir('./factors/'):
        os.system(f"cd factors && mkdir {setting.INFERENCE.FACTORS_SAVE_FILE.split('/')[1]}")
        
    if setting.MODEL == 'CNN5d':
        model = _M.CNN5d()
    else:
        model = _M.CNN20d()
    model.to(device)

    state_dict = torch.load(setting.TRAIN.MODEL_SAVE_FILE)
    model.load_state_dict(state_dict['model_state_dict'])

    factors = model_inference(model, setting)
    factors.to_csv(setting.INFERENCE.FACTORS_SAVE_FILE)