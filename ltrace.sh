#!/bin/sh

workload()
{
	echo "run workload"
}

setDrmTracingMark()
{
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/drm/tracing_mark_write/enable"
}

setTracing()
{

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_flip_request/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_flip_complete/enable"

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_evict/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_evict_everything/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_evict_vm/enable"

	# sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_change_domain/enable"
	# sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_clflush/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_create/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_destroy/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_fault/enable"
	# sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_pread/enable"
	# sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_object_pwrite/enable"

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_add/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_complete/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_notify/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_retire/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_wait_begin/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_request_wait_end/enable"

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_ring_dispatch/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_ring_flush/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_ring_queue/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_gem_ring_sync_to/enable"


	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_ring_wait_begin/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_ring_wait_end/enable"

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_destroy/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_fly/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_irq/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_landing/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_node_state_change/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_pop_from_queue/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_queue/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_remove/enable"
	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/i915_scheduler_unfly/enable"

	 sudo sh -c "echo $1 > /sys/kernel/debug/tracing/events/i915/intel_gpu_freq_change/enable"
}

main()
{
	if [ $# -ne 1 ]
	then
		echo "Error: Require trace file path"
		return
	fi

	#setTracing 1
	#setDrmTracingMark 1

	#workload

	#python systrace.py --time=10 -b 60000 sched gfx video -o $1

	sudo ./ltrace/ltrace -t 10 -z > tmp.zip
	python systrace.py --from-file=tmp.zip -o $1

	./ltrace/ltraceParser.py -f $1

	#setDrmTracingMark 0
	#setTracing 0
}

main "$@"

