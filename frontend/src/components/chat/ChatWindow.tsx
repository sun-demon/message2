import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Paper,
  Typography,
  Avatar,
  CircularProgress,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  EmojiEmotions as EmojiIcon,
  MoreVert as MoreVertIcon,
  Done as DoneIcon,
  DoneAll as DoneAllIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';
import { useChatStore } from '../../store/chatStore';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Message } from '../../types';

const ChatWindow: React.FC = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [selectedMessage, setSelectedMessage] = useState<number | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { activeChat, sendMessage, markAsRead } = useChatStore();
  const { sendTyping, isConnected } = useWebSocket();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (activeChat) {
      loadMessages();
    }
  }, [activeChat]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    setLoading(true);
    try {
      // Загрузка сообщений из API
      const response = await fetch(`/api/chats/${activeChat}/messages`);
      const data = await response.json();
      setMessages(data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim() || !activeChat) return;

    const newMessage = {
      chatId: activeChat,
      content: message,
      type: 'text',
    };

    try {
      await sendMessage(newMessage);
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTyping = () => {
    if (activeChat) {
      sendTyping(activeChat);
    }
  };

  const handleMessageMenu = (event: React.MouseEvent<HTMLElement>, messageId: number) => {
    setAnchorEl(event.currentTarget);
    setSelectedMessage(messageId);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setSelectedMessage(null);
  };

  const formatMessageTime = (date: string) => {
    return format(new Date(date), 'HH:mm', { locale: ru });
  };

  const formatMessageDate = (date: string) => {
    const messageDate = new Date(date);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (messageDate.toDateString() === today.toDateString()) {
      return 'Сегодня';
    } else if (messageDate.toDateString() === yesterday.toDateString()) {
      return 'Вчера';
    } else {
      return format(messageDate, 'd MMMM', { locale: ru });
    }
  };

  const groupMessagesByDate = () => {
    const groups: { [key: string]: Message[] } = {};
    messages.forEach(msg => {
      const date = formatMessageDate(msg.createdAt);
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(msg);
    });
    return groups;
  };

  if (!activeChat) {
    return (
      <Box
        sx={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 2,
          bgcolor: '#292730',
        }}
      >
        <Typography variant="h6" color="text.secondary">
          Выберите чат, чтобы начать общение
        </Typography>
      </Box>
    );
  }

  const messageGroups = groupMessagesByDate();

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: '#292730',
        position: 'relative',
      }}
    >
      {/* Область сообщений */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          '&::-webkit-scrollbar': {
            width: '6px',
          },
          '&::-webkit-scrollbar-track': {
            background: '#292730',
          },
          '&::-webkit-scrollbar-thumb': {
            background: '#8774e1',
            borderRadius: '3px',
          },
        }}
      >
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', pt: 2 }}>
            <CircularProgress sx={{ color: '#8774e1' }} />
          </Box>
        ) : (
          Object.entries(messageGroups).map(([date, msgs]) => (
            <Box key={date}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  my: 2,
                }}
              >
                <Paper
                  sx={{
                    px: 2,
                    py: 0.5,
                    bgcolor: '#36333d',
                    borderRadius: 2,
                  }}
                >
                  <Typography variant="caption" color="text.secondary">
                    {date}
                  </Typography>
                </Paper>
              </Box>

              {msgs.map((msg, index) => {
                const isOutgoing = msg.senderId === 'current-user'; // Замените на реальную проверку
                const showAvatar = index === 0 || msgs[index - 1].senderId !== msg.senderId;

                return (
                  <Box
                    key={msg.id}
                    sx={{
                      display: 'flex',
                      justifyContent: isOutgoing ? 'flex-end' : 'flex-start',
                      mb: 1,
                    }}
                  >
                    <Box
                      sx={{
                        display: 'flex',
                        maxWidth: '70%',
                        flexDirection: isOutgoing ? 'row-reverse' : 'row',
                        alignItems: 'flex-end',
                      }}
                    >
                      {!isOutgoing && showAvatar && (
                        <Avatar
                          src={msg.sender?.avatar}
                          sx={{
                            width: 32,
                            height: 32,
                            mr: 1,
                            mb: 1,
                            border: '2px solid #8774e1',
                          }}
                        >
                          {msg.sender?.name?.[0]}
                        </Avatar>
                      )}

                      <Box>
                        {!isOutgoing && !showAvatar && (
                          <Box sx={{ width: 32, mr: 1 }} />
                        )}

                        <Tooltip title={formatMessageTime(msg.createdAt)}>
                          <Paper
                            onContextMenu={(e) => {
                              e.preventDefault();
                              handleMessageMenu(e, msg.id);
                            }}
                            sx={{
                              p: 1.5,
                              bgcolor: isOutgoing ? '#8774e1' : '#2e2a33',
                              borderRadius: 2,
                              borderBottomRightRadius: isOutgoing ? 4 : 2,
                              borderBottomLeftRadius: !isOutgoing ? 4 : 2,
                              maxWidth: '100%',
                              wordBreak: 'break-word',
                              position: 'relative',
                              transition: 'all 0.2s',
                              '&:hover': {
                                filter: 'brightness(1.1)',
                              },
                            }}
                          >
                            <Typography variant="body1" sx={{ color: '#fff' }}>
                              {msg.content}
                            </Typography>

                            <Box
                              sx={{
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'flex-end',
                                gap: 0.5,
                                mt: 0.5,
                              }}
                            >
                              <Typography
                                variant="caption"
                                sx={{
                                  color: 'rgba(255,255,255,0.7)',
                                  fontSize: '0.7rem',
                                }}
                              >
                                {formatMessageTime(msg.createdAt)}
                              </Typography>

                              {isOutgoing && (
                                <>
                                  {msg.isRead ? (
                                    <DoneAllIcon
                                      sx={{
                                        fontSize: 16,
                                        color: '#4caf50',
                                      }}
                                    />
                                  ) : msg.isDelivered ? (
                                    <DoneAllIcon
                                      sx={{
                                        fontSize: 16,
                                        color: 'rgba(255,255,255,0.5)',
                                      }}
                                    />
                                  ) : (
                                    <DoneIcon
                                      sx={{
                                        fontSize: 16,
                                        color: 'rgba(255,255,255,0.5)',
                                      }}
                                    />
                                  )}
                                </>
                              )}
                            </Box>
                          </Paper>
                        </Tooltip>
                      </Box>
                    </Box>
                  </Box>
                );
              })}
            </Box>
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>

      {/* Индикатор печатания */}
      <Box sx={{ px: 2, pb: 1 }}>
        <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
          {isConnected && 'печатает...'}
        </Typography>
      </Box>

      {/* Поле ввода */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          bgcolor: '#2e2a33',
          borderTop: '1px solid rgba(135, 116, 225, 0.1)',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton
            size="small"
            sx={{
              color: '#8774e1',
              '&:hover': {
                background: 'rgba(135, 116, 225, 0.1)',
              },
            }}
          >
            <AttachFileIcon />
          </IconButton>

          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Написать сообщение..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            onKeyDown={handleTyping}
            variant="outlined"
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                bgcolor: '#36333d',
                borderRadius: 3,
                '& fieldset': {
                  borderColor: 'transparent',
                },
                '&:hover fieldset': {
                  borderColor: '#8774e1',
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#8774e1',
                },
              },
            }}
          />

          <IconButton
            onClick={handleSendMessage}
            disabled={!message.trim()}
            sx={{
              bgcolor: '#8774e1',
              color: '#fff',
              '&:hover': {
                bgcolor: '#a08cff',
              },
              '&.Mui-disabled': {
                bgcolor: 'rgba(135, 116, 225, 0.3)',
              },
              width: 40,
              height: 40,
            }}
          >
            <SendIcon />
          </IconButton>

          <IconButton
            sx={{
              color: '#8774e1',
              '&:hover': {
                background: 'rgba(135, 116, 225, 0.1)',
              },
            }}
          >
            <EmojiIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Контекстное меню сообщения */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
        PaperProps={{
          sx: {
            bgcolor: '#2e2a33',
            border: '1px solid rgba(135, 116, 225, 0.1)',
          },
        }}
      >
        <MenuItem onClick={handleCloseMenu}>Ответить</MenuItem>
        <MenuItem onClick={handleCloseMenu}>Редактировать</MenuItem>
        <MenuItem onClick={handleCloseMenu}>Копировать</MenuItem>
        <MenuItem onClick={handleCloseMenu}>Удалить</MenuItem>
        <MenuItem onClick={handleCloseMenu}>Переслать</MenuItem>
      </Menu>
    </Box>
  );
};

export default ChatWindow;
