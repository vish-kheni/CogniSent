"""
Custom Keras layer shared between training (scripts/train_cnn.py) and
inference (app/services/model_registry.py).

Using a properly registered Layer subclass -- rather than a raw
`layers.Lambda(lambda x: ...)` -- is what makes this survive being
saved to .h5 and reloaded in a completely different Python process
(the FastAPI server). Lambda layers serialize their function's raw
bytecode and try to recover its closure/globals on load, which is
fragile across processes; a registered custom layer serializes as a
plain reference to this class instead, which Keras can reliably
reconstruct as long as this module is imported before loading.
"""
import tensorflow as tf
import keras


@keras.saving.register_keras_serializable(package="cognisent")
class PaddingMask(keras.layers.Layer):
    """Outputs a 0/1 mask: 1.0 for real (non-zero) tokens, 0.0 for padding."""

    def call(self, inputs):
        return tf.cast(tf.not_equal(inputs, 0), tf.float32)

    def compute_output_shape(self, input_shape):
        return input_shape
