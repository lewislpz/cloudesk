package health

import (
	"sync"
	"testing"
)

func TestStateStartsUnreadyAndCanDrain(t *testing.T) {
	t.Parallel()

	state := NewState()
	if state.IsReady() {
		t.Fatal("new state is ready before initialization")
	}

	state.MarkReady()
	if !state.IsReady() {
		t.Fatal("state is not ready after MarkReady")
	}

	state.MarkNotReady()
	if state.IsReady() {
		t.Fatal("state remains ready after MarkNotReady")
	}
}

func TestStateSupportsConcurrentProbeReads(t *testing.T) {
	t.Parallel()

	state := NewState()
	var waitGroup sync.WaitGroup
	for range 32 {
		waitGroup.Add(1)
		go func() {
			defer waitGroup.Done()
			for range 100 {
				state.MarkReady()
				_ = state.IsReady()
				state.MarkNotReady()
			}
		}()
	}
	waitGroup.Wait()
}
