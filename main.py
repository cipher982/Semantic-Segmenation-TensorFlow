import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
import time


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= \
LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (
        image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights

    vgg_tag                    = 'vgg16'
    vgg_input_tensor_name      = 'image_input:0'
    vgg_keep_prob_tensor_name  = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    graph = tf.get_default_graph()

    image_input = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob   = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out  = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out  = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out  = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)


    return image_input, keep_prob, layer3_out, layer4_out, layer7_out

tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function


    conv_1x1 = tf.layers.conv2d(vgg_layer7_out, num_classes, 1, padding='same',
                                kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    output   = tf.layers.conv2d_transpose(conv_1x1, 512, 4, strides=2, padding='same',
                                          kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))
  
    pool4_out_scaled = tf.multiply(vgg_layer4_out, 0.01, name='pool4_out_scaled')
    output   = tf.add(output, pool4_out_scaled)
    output   = tf.layers.conv2d_transpose(output, 256, 4, strides=2, padding='same',
                                          kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    pool3_out_scaled = tf.multiply(vgg_layer3_out, 0.0001, name='pool3_out_scaled')
    output   = tf.add(output, pool3_out_scaled)
    output   = tf.layers.conv2d_transpose(output, num_classes, 16, strides=8, padding='same',
                                          kernel_regularizer=tf.contrib.layers.l2_regularizer(1e-3))

    
    
    return output
    
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    logits = tf.reshape(nn_last_layer, (-1, num_classes))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits,
                                                                                   labels=correct_label))
    
    reg_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
    reg_constant = 0.01  # Choose an appropriate one.
    cross_entropy_loss = cross_entropy_loss + reg_constant * sum(reg_losses)
    
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate)
    train_op = optimizer.minimize(cross_entropy_loss)

    return logits, train_op, cross_entropy_loss

tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function
    for epoch in range(epochs):
        start_time = time.time()
        for image, label in get_batches_fn(batch_size):
            feed = {input_image   : image,
                    correct_label : label,
                    keep_prob     : 0.3,
                    learning_rate : 1e-4}

            _, loss = sess.run([train_op, cross_entropy_loss], feed_dict=feed)

        elapsed_time = time.time() - start_time
        time_left = elapsed_time * (epochs - epoch - 1) / 60

        if epoch == 0:
            print("Training. . .")
            print("Epochs:{0} Dropout:{1} Learning Rate:{2}".\
                format(epochs, keep_prob, learning_rate))
        print("Loss: {0:.4f} at Epoch {1}/{2} in {3:.2f} seconds, time left: ~{4:.2f} minutes".\
            format(loss, epoch, epochs,elapsed_time, time_left))
        

tests.test_train_nn(train_nn)


def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = 'D:\data'
    runs_dir = 'D:\\runs'
    tests.test_for_kitti_dataset(data_dir)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results

        correct_label = tf.placeholder(tf.int32)
        learning_rate = tf.placeholder(tf.float32)
		
        epochs=40
        batch_size=15

        input_image, keep_prob, layer3_out, layer4_out, layer7_out = load_vgg(sess, vgg_path)

        layers_out = layers(layer3_out, layer4_out, layer7_out, num_classes)

        logits, train_op, cross_entropy_loss = optimize(layers_out, correct_label, 
                                                        learning_rate, num_classes)


        sess.run(tf.global_variables_initializer())
        train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
                 correct_label, keep_prob, learning_rate)


        #exit()
        print("Saving inference samples. . .")
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video
        saver = tf.train.Saver()
        save_path = os.path.join(runs_dir, 'model.ckpt')
        saver.save(sess, save_path)
        print("Saved at {0}".format(save_path))

        exit()


if __name__ == '__main__':
    run()
