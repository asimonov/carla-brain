from timeit import default_timer as timer

from styx_msgs.msg import TrafficLight

import tensorflow as tf
import numpy as np

from tl_label_converter import TLLabelConverter

class TLClassifier(object):
    def __init__(self, session):
        self._session = session
        self._label_converter = TLLabelConverter()
        # load graph
        self._classifier_graph_file = 'classifier_graph.pb'
        self._classifier_graph_scope = 'classifier'
        graph_def = tf.GraphDef()
        with open(self._classifier_graph_file, 'rb') as f:
            graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name=self._classifier_graph_scope)
        # inputs/outputs
        graph = self._session.graph
        self._classifier_input = graph.get_tensor_by_name(self._classifier_graph_scope+'/data/images:0')
        self._classifier_keep_prob = graph.get_tensor_by_name(self._classifier_graph_scope+'/dropout_keep_probability:0')
        self._classifier_softmax = graph.get_tensor_by_name(self._classifier_graph_scope+'/predictions/prediction_softmax:0')
        self._classifier_output = graph.get_tensor_by_name(self._classifier_graph_scope+'/predictions/prediction_class:0')
        # image size
        self._image_shape = (32, 32)
        # run on fake image once
        fake_img = np.zeros(self._image_shape+(3,), dtype=np.uint8)
        self.get_classification(fake_img)


    def get_classification(self, image):
        """Determines the color of the traffic light in the image

        Args:
            image (cv::Mat): image containing the traffic light

        Returns:
            int: ID of traffic light color (specified in styx_msgs/TrafficLight)

        """
        h, w, c = image.shape
        assert h==32 and w==32 and c==3

        # run TF prediction
        start_time = timer()
        ops = [self._classifier_softmax, self._classifier_output]
        feed_dict = {self._classifier_input: [image],
                     self._classifier_keep_prob: 1.0}
        predicted_probabilities, predicted_class = self._session.run(ops, feed_dict=feed_dict)
        predicted_label = self._label_converter.convert_to_labels(predicted_class)
        tf_time_ms = int((timer() - start_time) * 1000)

        result = TrafficLight.UNKNOWN
        if predicted_label=='red':
            result = TrafficLight.RED
        elif predicted_label=='yellow':
            result = TrafficLight.YELLOW
        elif predicted_label=='green':
            result = TrafficLight.GREEN

        return result


