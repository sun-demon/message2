import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Avatar,
  Badge,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import ChatList from './ChatList';
import ChatWindow from './ChatWindow';
import { useChatStore } from '../../store/chatStore';

const DRAWER_WIDTH = 360;

const ChatLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { activeChat, setActiveChat, chats } = useChatStore();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  useEffect(() => {
    if (!isMobile) {
      setMobileOpen(false);
    }
  }, [isMobile]);

  const activeChatData = chats.find(chat => chat.id === activeChat);

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: '#292730' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          ml: { md: `${DRAWER_WIDTH}px` },
          bgcolor: '#2e2a33',
          borderBottom: '1px solid rgba(135, 116, 225, 0.1)',
          boxShadow: 'none',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          {activeChatData && (
            <>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                variant="dot"
                color={activeChatData.isOnline ? 'success' : 'default'}
                sx={{ mr: 2 }}
              >
                <Avatar
                  src={activeChatData.avatar}
                  sx={{
                    width: 40,
                    height: 40,
                    border: '2px solid #8774e1',
                  }}
                >
                  {activeChatData.name?.[0]}
                </Avatar>
              </Badge>

              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {activeChatData.name}
                </Typography>
                {activeChatData.isOnline && (
                  <Typography variant="caption" color="success.main">
                    в сети
                  </Typography>
                )}
              </Box>
            </>
          )}

          <IconButton color="inherit">
            <SearchIcon />
          </IconButton>
          <IconButton color="inherit">
            <MoreVertIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { md: DRAWER_WIDTH }, flexShrink: { md: 0 } }}
      >
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                bgcolor: '#2e2a33',
                borderRight: '1px solid rgba(135, 116, 225, 0.1)',
              },
            }}
          >
            <ChatList onChatSelect={() => setMobileOpen(false)} />
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: DRAWER_WIDTH,
                bgcolor: '#2e2a33',
                borderRight: '1px solid rgba(135, 116, 225, 0.1)',
                position: 'relative',
              },
            }}
            open
          >
            <ChatList />
          </Drawer>
        )}
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <Toolbar />
        <ChatWindow />
      </Box>
    </Box>
  );
};

export default ChatLayout;