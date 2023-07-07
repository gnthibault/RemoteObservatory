

class DifferentialPointer:
    def __init__(self, config=None):
        super().__init__()
        if config is None:
            config = dict(
                gen_hips=False
            )

        self.gen_hips = config["gen_hips"]

    def points(self):
        pass