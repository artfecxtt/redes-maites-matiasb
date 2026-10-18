from socketUDP import SocketUDP
from slidingWindowCC import SlidingWindowCC

# 0 es slow start, 1 es congestion avoidance
class CongestionControl:
    def __init__(self, MSS: int):
        self.current_state = 0
        self.MSS = MSS
        self.cwnd = self.MSS
        self.ssthresh = None

    def get_cwnd(self):
        return self.cwnd

    def get_MSS_in_cwnd(self):
        return int(self.get_cwnd() // self.MSS)

    def event_ack_received(self):
        if self.is_state_slow_start():
            self.cwnd += self.MSS
            if self.ssthresh is not None and self.cwnd >= self.ssthresh:
                self.current_state = 1
                
        elif self.is_state_congestion_avoidance():
            mss_contador = self.get_MSS_in_cwnd()
            if mss_contador > 0:
                self.cwnd += self.MSS/mss_contador
            else:
                self.cwnd += self.MSS

    def event_timeout(self):
        self.ssthresh = int(self.get_cwnd()/2)
        self.cwnd = self.MSS
        self.current_state = 0

    def is_state_slow_start(self):
        if self.current_state == 0:
            return True
        else:
            return False

    def is_state_congestion_avoidance(self):
        if self.current_state == 1:
            return True
        else:
            return False

    def get_ssthresh(self):
        return self.ssthresh
