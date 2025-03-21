:py:mod:`quark.onnx.quantization.config.config`
===============================================

.. py:module:: quark.onnx.quantization.config.config

.. autoapi-nested-parse::

   Quark Quantization Config API for ONNX



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   quark.onnx.quantization.config.config.Config
   quark.onnx.quantization.config.config.QuantizationConfig




.. py:class:: Config


   A class that encapsulates comprehensive quantization configurations for a machine learning model, allowing for detailed and hierarchical control over quantization parameters across different model components.

   :param QuantizationConfig global_quant_config: Global quantization configuration applied to the entire model unless overridden at the layer level.


.. py:class:: QuantizationConfig


   A data class that specifies quantization configurations for different components of a module, allowing hierarchical control over how each tensor type is quantized.

   Attributes:
       calibrate_method (Union[CalibrationMethod, PowerOfTwoMethod]): Method used for calibration. Default is CalibrationMethod.MinMax.
       quant_format (Union[QuantFormat, VitisQuantFormat]): Format of quantization. Default is QuantFormat.QDQ.
       activation_type (Union[QuantType, VitisQuantType]): Type of quantization for activations. Default is QuantType.QInt8.
       weight_type (Union[QuantFormat, VitisQuantFormat]): Type of quantization for weights. Default is QuantType.QInt8.

       input_nodes (List[str]): List of input nodes to be quantized. Default is an empty list.
       output_nodes (List[str]): List of output nodes to be quantized. Default is an empty list.
       op_types_to_quantize (List[str]): List of operation types to be quantized. Default is an empty list.
       extra_op_types_to_quantize (List[str]): List of additional operation types to be quantized. Default is an empty list.
       nodes_to_quantize (List[str]): List of node names to be quantized. Default is an empty list.
       nodes_to_exclude (List[str]): List of node names to be excluded from quantization. Default is an empty list.
       subgraphs_to_exclude (List[Tuple[List[str]]]): List of start and end node names of subgraphs to be excluded from quantization. Default is an empty list.

       specific_tensor_precision (bool): Flag to enable specific tensor precision. Default is False.
       execution_providers (List[str]): List of execution providers. Default is ['CPUExecutionProvider'].

       per_channel (bool): Flag to enable per-channel quantization. Default is False.
       reduce_range (bool): Flag to reduce quantization range. Default is False.
       optimize_model (bool): Flag to optimize the model. Default is True.
       use_dynamic_quant (bool): Flag to use dynamic quantization. Default is False.
       use_external_data_format (bool): Flag to use external data format. Default is False.

       convert_fp16_to_fp32 (bool): Flag to convert FP16 to FP32. Default is False.
       convert_nchw_to_nhwc (bool): Flag to convert NCHW to NHWC. Default is False.

       include_sq (bool): Flag to include square root in quantization. Default is False.
       include_cle (bool): Flag to include CLE in quantization. Default is False.
       include_auto_mp (bool): Flag to include automatic mixed precision. Default is False.
       include_fast_ft (bool): Flag to include fast fine-tuning. Default is False.

       enable_npu_cnn (bool): Flag to enable NPU CNN. Default is False.
       enable_npu_transformer (bool): Flag to enable NPU Transformer. Default is False.

       debug_mode (bool): Flag to enable debug mode. Default is False.
       print_summary (bool): Flag to print summary of quantization. Default is True.
       ignore_warnings: (bool): Flag to suppress the warnings globally. Default is True.
       log_severity_level (int): 0:DEBUG, 1:INFO, 2:WARNING. 3:ERROR, 4:CRITICAL/FATAL. Default is 1.

       extra_options (Dict[str, Any]): Dictionary for additional options. Default is an empty dictionary.


