from __future__ import print_function

import json

import fire
import numpy as np
from sklearn.metrics import f1_score, confusion_matrix, accuracy_score
from tqdm import tqdm

from model.architectures import get_classifier
from data.preprocess import BioNLPPreprocessor
try:                import cPickle as pickle
except ImportError: import _pickle as pickle


def predict(model, preprocessor, data, output_path, batch_size=70):

    data = [item for item in data if not preprocessor.skip_sample(item)]
    eval_predictions = []
    eval_labels = [preprocessor.get_label(sample) for sample in data]
    for batch_start in tqdm(range(0, len(data), batch_size)):
        batch = data[batch_start: batch_start + batch_size]
        data_input = preprocessor.parse(data=batch)
        data_input = data_input[:-1]    # Last axis contains real labels

        probabilities = model.predict(data_input)
        predictions = np.argmax(probabilities, axis=1)
        eval_predictions += list(predictions.flatten())
        for sample, prediction, probability in zip(batch, predictions, probabilities):
            sample['prediction'] = int(prediction)
            sample['probabilities'] = probability.tolist()

    print('Confusion Matrix:\n', confusion_matrix(eval_labels, eval_predictions))
    print('F score:', f1_score(eval_labels, eval_predictions))
    print('Accuracy:', accuracy_score(eval_labels, eval_predictions))

    data = {item.pop('id'): item for item in data}
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=True)


def main(model_path, batch_size=80, dataset='bionlp', processor_path='data/valid_processor.pkl',
         input_path='data/bionlp_test_data.json', output_path='data/out_bionlp_test_data.json',
         interaction=None):

    if dataset == 'bionlp':
        with open(processor_path, 'rb') as f:
            preprocessor = pickle.load(f)
        if interaction:
            if interaction == '__all__':    preprocessor.valid_interactions = None
            else:                           preprocessor.valid_interactions = {interaction}
        data = preprocessor.load_data(input_path)
    else:
        raise ValueError('Could not find implementation for specified dataset')

    model = get_classifier(model_path=model_path)
    predict(model=model,
            preprocessor=preprocessor,
            data=data,
            output_path=output_path,
            batch_size=batch_size)


if __name__ == '__main__':
    fire.Fire(main)
