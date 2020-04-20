import torch
import torch.nn as nn
from model.kcnn import KCNN
from model.attention import Attention


class DKN(torch.nn.Module):
    """
    Deep knowledge-aware network.
    Input a candidate news and a list of user clicked news, produce the click probability.
    """

    def __init__(self, config, embeddings):
        super(DKN, self).__init__()
        self.config = config
        self.kcnn = KCNN(config, embeddings)
        if self.config.use_attention:
            self.attention = Attention(config)
        # TODO parameters
        self.dnn = nn.Sequential(
            nn.Linear(
                len(self.config.window_sizes) * 2 * self.config.num_filters,
                16), nn.Linear(16, 1))

    def forward(self, candidate_news, clicked_news):
        """
        Args:
          candidata_news:
            {
                "word": [Tensor(batch_size) * num_words_a_sentence],
                "entity":[Tensor(batch_size) * num_words_a_sentence]
            }
          clicked_news:
            [
                {
                    "word": [Tensor(batch_size) * num_words_a_sentence],
                    "entity":[Tensor(batch_size) * num_words_a_sentence]
                } * num_clicked_news_a_user
            ]
        Returns:
          [probability] * batch_size
        """
        # batch_size, len(window_sizes) * num_filters
        candidate_news_vector = self.kcnn(candidate_news)
        # num_clicked_news_a_user, batch_size, len(window_sizes) * num_filters
        clicked_news_vector = torch.stack([self.kcnn(x) for x in clicked_news])
        # batch_size, len(window_sizes) * num_filters
        if self.config.use_attention:
            user_vector = self.attention(candidate_news_vector,
                                         clicked_news_vector)
        else:
            user_vector = clicked_news_vector.mean(dim=0)
        # batch_size
        click_probability = torch.sigmoid(
            self.dnn(torch.cat((user_vector, candidate_news_vector),
                               dim=1)).squeeze(dim=1))
        return click_probability
