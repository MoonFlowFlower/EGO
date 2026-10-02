# v0.3 实测：小网络的流式预测与动作选择

这是合成数值场景，不是自然语言、社会推理或终身学习证据。每个方法读取同一随机日志，在标签揭示前预测。最后三分之一的结果如下；数值较低的误差/遗憾较好。

|场景|方法|后段误差|后段选择遗憾|后段最优选择率|
|---|---|---:|---:|---:|
|stationary|neural_replay|0.04956|0.17504|50.3%|
|stationary|neural_no_replay|0.05665|0.18718|50.6%|
|stationary|linear_online|0.05823|0.18095|50.8%|
|stationary|nearest_cache|0.00523|0.00304|96.1%|
|stationary|frozen|0.04361|0.18889|46.4%|
|stationary|random|0.04361|0.16234|54.4%|
|reversal|neural_replay|0.05058|0.17564|51.7%|
|reversal|neural_no_replay|0.05611|0.18144|50.0%|
|reversal|linear_online|0.05766|0.17073|51.9%|
|reversal|nearest_cache|0.03716|0.11511|65.0%|
|reversal|frozen|0.04361|0.15615|53.6%|
|reversal|random|0.04361|0.18270|45.6%|

stationary：映射稳定；reversal：中途关系反转，变化标记不提供给任何模型。nearest_cache 是容量192的近邻缓存；linear_online 获得相同输入和9次更新。冻结/随机是下界参考，不是最强基线。

这组结果只支持或反驳该流式学习组件的有限表现；不能推出完整认知架构比普通LLM更好。没有把评测的真实函数提供给模型。
