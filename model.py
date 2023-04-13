# each day is displayed in 3 pixels
# use cnn to predict 
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np
import enum

class MODEL_INPUT(enum.Enum):
    FIVE_DAYS = 1
    TWENTY_DAYS = 2

class MODEL_OUTPUT(enum.Enum):
    ONE_DAY = 1
    FIVE_DAYS = 2

class CNN5d(nn.Module):
    # input in shape of N*32*15
    # output in shape of N*1
    def __init__(self):
        super(CNN5d, self).__init__()
        # conv1 is 5x3 conv, 64
        # conv2 is 5x3 conv, 128
        self.conv1 = nn.Conv2d(1, 64, (5, 3), padding=(2, 1))
        self.conv2 = nn.Conv2d(64, 128, (5, 3), padding=(2, 1))
        self.fc1 = nn.Linear(15360, 1)

    def forward(self, x):
        # input: N * 1 * 32 * 15
        x = F.relu(self.conv1(x))   # output: N * 64 * 32 * 15
        x = F.max_pool2d(x, (2, 1)) # output: N * 64 * 16 * 15
        x = F.relu(self.conv2(x))   # output: N * 128 * 16 * 15
        x = F.max_pool2d(x, (2, 1)) # output: N * 128 * 8 * 15
        x = x.view(-1, 15360)       # output: N * 15360
        x = self.fc1(x)             # output: N * 1
        x = F.softmax(x, dim=1)     # output: N * 1
        return x
    
class CNN20d(nn.Module):
    # input in shape of N*64*60
    # output in shape of N*1
    # with 3 conv layers
    def __init__(self):
        super(CNN20d, self).__init__()
        self.conv1 = nn.Conv2d(1, 64, (5, 3), padding=1)
        self.conv2 = nn.Conv2d(64, 128, (5, 3), padding=1)
        self.conv3 = nn.Conv2d(128, 256, (5, 3), padding=1)
        self.fc1 = nn.Linear(46080, 1)

    def forward(self, x):
        # input: N * 1 * 64 * 60
        x = F.relu(self.conv1(x))   # output: N * 64 * 62 * 60
        x = F.max_pool2d(x, (2, 1)) # output: N * 64 * 31 * 60
        x = F.relu(self.conv2(x))   # output: N * 128 * 29 * 60
        x = F.max_pool2d(x, (2, 1)) # output: N * 128 * 14 * 60
        x = F.relu(self.conv3(x))   # output: N * 256 * 12 * 60
        x = F.max_pool2d(x, (2, 1)) # output: N * 256 * 6 * 60
        x = x.view(-1, 46080)       # output: N * 46080
        x = self.fc1(x)             # output: N * 1
        x = F.softmax(x, dim=1)     # output: N * 1
        return x

def train_model(model, train_loader, val_loader, num_epochs=10, learning_rate=0.001, batch_size=32, device='cpu', weight_decay=0.0):
    model = model.to(device)
    # train model
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    loss_func = nn.BCELoss().to(device)
    for epoch in range(num_epochs):
        # training
        model.train()
        for i, data in enumerate(train_loader):
            inputs, labels = data
            inputs = inputs.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = loss_func(outputs, labels)
            loss.backward()
            optimizer.step()
        print('| Epoch: %d | Loss: %.4f |' % (epoch, loss.item()))

        # validation
        v_loss = 0
        v_accu = 0
        model.eval()
        for i, data in enumerate(val_loader):
            inputs, labels = data
            inputs = inputs.float().to(device)
            labels = labels.float().to(device)
            outputs = model(inputs)
            loss = loss_func(outputs, labels)
            v_loss += loss.item()
            v_accu += torch.sum(torch.abs(outputs - labels) < 0.5).item()
        v_loss /= len(val_loader)
        v_accu /= len(val_loader) * batch_size
        print('| Validation Loss: %.4f | Accuracy: %.4f |' % (v_loss, v_accu))

    return model

def test_model(model, test_loader, batch_size=32, device='cpu'):
    model = model.to(device)
    loss_func = nn.BCELoss().to(device)
    model.eval()
    t_loss = 0
    t_accu = 0
    for i, data in enumerate(test_loader):
        inputs, labels = data
        inputs = inputs.float().to(device)
        labels = labels.float().to(device)
        outputs = model(inputs)
        loss = loss_func(outputs, labels)
        t_loss += loss.item()
        t_accu += torch.sum(torch.abs(outputs - labels) < 0.5).item()
    t_loss /= len(test_loader)
    t_accu /= len(test_loader) * batch_size
    print('| Test Loss: %.4f | Accuracy: %.4f |' % (t_loss, t_accu))