import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  Divider,
  IconButton,
  InputAdornment,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Email as EmailIcon,
  QrCode as QRCodeIcon,
  Visibility,
  VisibilityOff,
  QrCode,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import logo from '/logo.svg';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Login: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [loginMethod, setLoginMethod] = useState<'phone' | 'email'>('phone');
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [qrToken, setQrToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const navigate = useNavigate();
  const { login } = useAuthStore();

  useEffect(() => {
    // Генерируем токен для QR-кода
    if (tabValue === 2) {
      generateQrToken();
    }
  }, [tabValue]);

  const generateQrToken = async () => {
    try {
      const response = await fetch('/api/auth/qr/token');
      const data = await response.json();
      setQrToken(data.token);
    } catch (err) {
      setError('Не удалось получить QR-код');
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setError('');
  };

  const handleLoginMethodChange = (method: 'phone' | 'email') => {
    setLoginMethod(method);
    setIdentifier('');
    setError('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(identifier, password, loginMethod);
      navigate('/chats');
    } catch (err: any) {
      setError(err.message || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: '#292730',
        backgroundImage: 'radial-gradient(circle at 10% 20%, rgba(135, 116, 225, 0.1) 0%, transparent 30%)',
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            p: 4,
            borderRadius: 4,
            background: '#2e2a33',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(135, 116, 225, 0.1)',
          }}
        >
          {/* Логотип */}
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Box
              component="img"
              src={logo}
              alt="Message2"
              sx={{
                width: 80,
                height: 80,
                filter: 'drop-shadow(0 4px 8px rgba(135, 116, 225, 0.3))',
              }}
            />
            <Typography
              variant="h4"
              sx={{
                mt: 2,
                fontWeight: 600,
                background: 'linear-gradient(135deg, #8774e1 0%, #a08cff 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Message2
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Войдите, чтобы продолжить общение
            </Typography>
          </Box>

          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{
              mb: 2,
              '& .MuiTab-root': {
                color: 'text.secondary',
                '&.Mui-selected': {
                  color: '#8774e1',
                },
              },
              '& .MuiTabs-indicator': {
                backgroundColor: '#8774e1',
              },
            }}
          >
            <Tab icon={<PhoneIcon />} label="Телефон" />
            <Tab icon={<EmailIcon />} label="Email" />
            <Tab icon={<QRCodeIcon />} label="QR-код" />
          </Tabs>

          {/* Вход по телефону/email */}
          <TabPanel value={tabValue} index={0}>
            <Box sx={{ mb: 2 }}>
              <Button
                variant={loginMethod === 'phone' ? 'contained' : 'outlined'}
                onClick={() => handleLoginMethodChange('phone')}
                sx={{ mr: 1, borderRadius: 2 }}
              >
                Телефон
              </Button>
              <Button
                variant={loginMethod === 'email' ? 'contained' : 'outlined'}
                onClick={() => handleLoginMethodChange('email')}
                sx={{ borderRadius: 2 }}
              >
                Email
              </Button>
            </Box>

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label={loginMethod === 'phone' ? 'Номер телефона' : 'Email'}
                variant="outlined"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder={loginMethod === 'phone' ? '+7 (999) 123-45-67' : 'example@mail.com'}
                sx={{
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    '& fieldset': {
                      borderColor: 'rgba(135, 116, 225, 0.3)',
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

              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="Пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    '& fieldset': {
                      borderColor: 'rgba(135, 116, 225, 0.3)',
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

              {error && (
                <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                  {error}
                </Alert>
              )}

              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loading}
                sx={{
                  py: 1.5,
                  fontSize: '1rem',
                  background: '#8774e1',
                  '&:hover': {
                    background: '#a08cff',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} /> : 'Войти'}
              </Button>

              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Нет аккаунта?{' '}
                  <Button
                    onClick={() => navigate('/register')}
                    sx={{
                      color: '#8774e1',
                      textTransform: 'none',
                      '&:hover': {
                        background: 'transparent',
                        textDecoration: 'underline',
                      },
                    }}
                  >
                    Зарегистрироваться
                  </Button>
                </Typography>
              </Box>
            </form>
          </TabPanel>

          {/* Вход по QR-коду */}
          <TabPanel value={tabValue} index={2}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="body1" sx={{ mb: 3, color: 'text.secondary' }}>
                Отсканируйте QR-код в приложении Message2
              </Typography>

              <Box
                sx={{
                  display: 'inline-block',
                  p: 2,
                  bgcolor: 'white',
                  borderRadius: 4,
                  boxShadow: '0 8px 16px rgba(0,0,0,0.3)',
                  mb: 3,
                }}
              >
                {qrToken ? (
                  <QrCode
                    value={qrToken}
                    size={240}
                    level="H"
                    includeMargin
                    imageSettings={{
                      src: logo,
                      x: undefined,
                      y: undefined,
                      height: 50,
                      width: 50,
                      excavate: true,
                    }}
                  />
                ) : (
                  <CircularProgress />
                )}
              </Box>

              <Typography variant="body2" color="text.secondary">
                QR-код обновляется каждые 60 секунд
              </Typography>

              <Button
                variant="outlined"
                onClick={generateQrToken}
                sx={{
                  mt: 2,
                  borderColor: '#8774e1',
                  color: '#8774e1',
                  '&:hover': {
                    borderColor: '#a08cff',
                    background: 'rgba(135, 116, 225, 0.1)',
                  },
                }}
              >
                Обновить QR-код
              </Button>
            </Box>
          </TabPanel>
        </Paper>
      </Container>
    </Box>
  );
};

export default Login;
